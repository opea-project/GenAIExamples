# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import functools
import os
import re
from enum import Enum
from queue import Empty
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Tuple, Union

import ray
import torch
from fastapi import HTTPException
from pydantic import BaseModel
from ray import serve
from rayllm.api_openai_backend.openai_protocol import ChatMessage, ErrorResponse, ModelResponse
from rayllm.api_openai_backend.tools import ChatPromptCapture, OpenAIToolsPrompter
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

DEVICE_CPU = "cpu"
DEVICE_HPU = "hpu"


def load_tokenizer(model, tokenizer_name_or_path):
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name_or_path)
    if not model.config.is_encoder_decoder:
        tokenizer.padding_side = "left"
    # Some models like GPT2 do not have a PAD token so we have to set it if necessary
    if model.config.model_type == "llama":
        # unwind broken decapoda-research config
        model.generation_config.pad_token_id = 0
        model.generation_config.bos_token_id = 1
        model.generation_config.eos_token_id = 2
        tokenizer.bos_token_id = model.generation_config.bos_token_id
        tokenizer.eos_token_id = model.generation_config.eos_token_id
        tokenizer.pad_token_id = model.generation_config.pad_token_id
        tokenizer.pad_token = tokenizer.decode(tokenizer.pad_token_id)
        tokenizer.eos_token = tokenizer.decode(tokenizer.eos_token_id)
        tokenizer.bos_token = tokenizer.decode(tokenizer.bos_token_id)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.generation_config.pad_token_id = model.generation_config.eos_token_id

    return tokenizer


class PromptFormat(Enum):
    CHAT_FORMAT = 1
    PROMPTS_FORMAT = 2
    INVALID_FORMAT = 3


def get_prompt_format(input: Union[List[str], List[dict], List[ChatMessage]]):
    chat_format = True
    prompts_format = True
    for item in input:
        if isinstance(item, str) or isinstance(item, list):
            chat_format = False
        elif isinstance(item, dict) or isinstance(item, ChatMessage):
            prompts_format = False
        else:
            chat_format = False
            prompts_format = False
            break
    if chat_format:
        return PromptFormat.CHAT_FORMAT
    if prompts_format:
        return PromptFormat.PROMPTS_FORMAT
    return PromptFormat.INVALID_FORMAT


class ChatModel:
    human_id = "<human>"
    bot_id = "<bot>"
    unknown_id = "<unknown>"
    MEANINGLESS_WORDS = ["<pad>", "</s>", "<|endoftext|>", "<br>"]
    stop_words = ["<human>"]

    def __init__(self, intro, human_id, bot_id, stop_words) -> None:
        self.intro = intro
        self.human_id = human_id
        self.bot_id = bot_id
        self.stop_words = stop_words
        self.MEANINGLESS_WORDS.extend(self.stop_words)

    def prepare_prompt(self, messages: list):
        """Prepare prompt from history messages."""
        prompt = ""
        for msg in messages:
            role, content = msg.role, msg.content
            if role == "user":
                prompt += f"{self.human_id}: {content}\n"
            elif role == "assistant":
                prompt += f"{self.bot_id}: {content}\n"
            else:
                prompt += f"{self.unknown_id}: {content}\n"
        prompt += f"{self.bot_id}:"
        return prompt

    def convert_output(self, output: str):
        """Convert the model output to final answer."""
        human_id = self.human_id.strip()
        bot_id = self.bot_id.strip()
        if human_id != "":
            output = output.split(human_id)[0]
        if bot_id != "":
            output = output.split(bot_id)[0]
        for word in self.MEANINGLESS_WORDS:
            output = output.replace(word, "")
        text = output
        # remove partial human_id or bot id
        if "\n" in text and (
            human_id.startswith(text[text.rfind("\n") + 1 :]) or bot_id.startswith(text[text.rfind("\n") + 1])
        ):
            text = text[: text.rfind("\n")]
        return text

    def get_prompt(self, messages):
        """Generate response based on messages."""
        prompt = self.prepare_prompt(messages)
        return prompt


class ChatModelGptJ(ChatModel):
    def __init__(self, intro, human_id, bot_id, stop_words):
        super().__init__(intro, human_id, bot_id, stop_words)

    def prepare_prompt(self, messages: list):
        """Prepare prompt from history messages."""
        prompt = self.intro
        for msg in messages:
            msg = dict(msg)
            role, content = msg["role"], msg["content"]
            if role == "user":
                if self.human_id != "":
                    prompt += f"{self.human_id}:\n{content}\n"
                else:
                    prompt += f"{content}\n"
            elif role == "assistant":
                if self.bot_id != "":
                    prompt += f"{self.bot_id}:\n{content}\n"
                else:
                    prompt += f"{content}\n"
            else:
                prompt += f"### Unknown:\n{content}\n"
        if self.bot_id != "":
            prompt += f"{self.bot_id}:\n"
        return prompt


class ChatModelLLama(ChatModel):
    def __init__(self, intro="", human_id="<s>[INST] {msg} [/INST]", bot_id="", stop_words=[]):
        super().__init__(intro, human_id, bot_id, stop_words)

    def prepare_prompt(self, messages: list):
        """Prepare prompt from history messages."""
        prompt = self.intro
        for msg in messages:
            msg = dict(msg)
            role, content = msg["role"], msg["content"]
            if role == "user":
                if self.human_id != "":
                    prompt += self.human_id.format(msg=content)
                else:
                    prompt += f"{content}\n"
            elif role == "assistant":
                prompt += f"{content}\n"
            elif role == "tool":
                prompt += f"{content}\n"
            elif role == "system":
                prompt += f"### system:\n{content}\n"
            else:
                prompt += f"### Unknown:\n{content}\n"
        if self.bot_id != "":
            prompt += f"{self.bot_id}:\n"
        return prompt


class ChatModelGemma(ChatModel):
    def __init__(self, intro, human_id, bot_id, stop_words):
        super().__init__(intro, human_id, bot_id, stop_words)

    def prepare_prompt(self, messages: list):
        """Prepare prompt from history messages."""
        prompt = self.intro
        for msg in messages:
            msg = dict(msg)
            role, content = msg["role"], msg["content"]
            if role == "user":
                if self.human_id != "":
                    prompt += f"{self.human_id} {content}\n"
                else:
                    prompt += f"{content}\n"
            elif role == "assistant":
                if self.bot_id != "":
                    prompt += f"{self.bot_id} {content}\n"
                else:
                    prompt += f"{content}\n"
            else:
                prompt += f"### Unknown:\n{content}\n"
        if self.bot_id != "":
            prompt += f"{self.bot_id}:\n"
        return prompt


class ChatModelNoFormat(ChatModel):
    def __init__(self, intro, human_id, bot_id, stop_words):
        super().__init__(intro, human_id, bot_id, stop_words)

    def prepare_prompt(self, messages: list):
        """Prepare prompt from history messages."""
        prompt = ""
        for msg in messages:
            msg = dict(msg)
            prompt += msg["content"]
        return prompt


class GenerateResult(BaseModel):
    text: str = ""
    input_length: int = None
    generate_length: int = None


class Predictor:
    def __init__(self, infer_conf: dict) -> None:
        model_id_or_path = infer_conf["model_id_or_path"]
        use_auth_token = infer_conf["use_auth_token"]
        trust_remote_code = infer_conf["trust_remote_code"]

        device = os.environ.get("DEVICE", "hpu")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id_or_path, use_auth_token=use_auth_token, trust_remote_code=trust_remote_code
        )
        self.device = torch.device(device)
        # now deepspeed predictor don't have the model
        # so configure_tokenizer cannot be called
        # this should be solved in the next pr
        # where it is also a worker
        # This can be removed then
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.input_length = None

    def tokenize_inputs(self, text):
        input_tokens = self.tokenizer(text, return_tensors="pt", padding=True)
        input_ids = input_tokens.input_ids
        self.input_length = input_ids.size()[1]
        input_ids = input_ids.to(device=self.device)
        return input_ids, self.input_length

    def configure_tokenizer(self, model_name):
        model = self.model
        tokenizer = self.tokenizer
        if re.search("llama", model.config.architectures[0], re.IGNORECASE):
            # unwind broken decapoda-research config
            model.generation_config.pad_token_id = 0
            model.generation_config.bos_token_id = 1
            model.generation_config.eos_token_id = 2

        if (
            hasattr(model.generation_config, "pad_token_id")
            and model.generation_config.pad_token_id is not None
            and "chatglm" not in model_name
        ):
            tokenizer.pad_token_id = model.generation_config.pad_token_id
        if (
            hasattr(model.generation_config, "eos_token_id")
            and model.generation_config.eos_token_id is not None
            and "chatglm" not in model_name
        ):
            tokenizer.eos_token_id = model.generation_config.eos_token_id
        if hasattr(model.generation_config, "bos_token_id") and model.generation_config.bos_token_id is not None:
            tokenizer.bos_token_id = model.generation_config.bos_token_id

        if tokenizer.pad_token_id is None:
            model.generation_config.pad_token_id = tokenizer.pad_token_id = tokenizer.eos_token_id

        if model.generation_config.eos_token_id is None:
            model.generation_config.eos_token_id = tokenizer.eos_token_id

        if not model.config.is_encoder_decoder:
            tokenizer.padding_side = "left"

        if tokenizer.pad_token is None and tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
            model.generation_config.pad_token_id = model.generation_config.eos_token_id

    def generate(self, prompts: Union[str, List[str]], **config) -> Union[GenerateResult, List[GenerateResult], None]:
        pass

    async def generate_async(self, prompts: Union[str, List[str]], **config) -> Union[str, List[str]]:
        pass

    # output is streamed into streamer
    def streaming_generate(self, prompt: str, streamer, **config) -> None:
        pass

    def get_streamer(self):
        pass

    async def stream_results(self, results_generator) -> AsyncGenerator[str, None]:
        pass


class HPUPredictor(Predictor):
    def __init__(self, infer_conf: dict):
        super().__init__(infer_conf)

        model_id_or_path = infer_conf["model_id_or_path"]
        use_auth_token = infer_conf["use_auth_token"]
        trust_remote_code = infer_conf["trust_remote_code"]
        self.cpus_per_worker = infer_conf["num_cpus_per_worker"]
        self.hpus_per_worker = infer_conf["num_hpus_per_worker"]
        # decide correct torch type for loading HF model
        self.use_lazy_mode = True
        self.use_hpu_graphs = False
        # TODO add torch_compile, i.e. hpu specific configs. including quant
        # if args.torch_compile and model.config.model_type == "llama":
        #     self.use_lazy_mode = False

        from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

        # Tweak transformer to optimize performance on Gaudi
        adapt_transformers_to_gaudi()
        # Not using DeepSpeed, load model locally
        self.device = torch.device("hpu")
        model = AutoModelForCausalLM.from_pretrained(
            model_id_or_path, use_auth_token=use_auth_token, trust_remote_code=trust_remote_code
        )
        self.model = model.eval().to(self.device)
        if self.use_hpu_graphs:
            from habana_frameworks.torch.hpu import wrap_in_hpu_graph  # pylint: disable=E0401

            self.model = wrap_in_hpu_graph(self.model)
        else:
            print("Warning: use_hpu_graphs is set to False. This will hurt the performance.")
        self.tokenizer = load_tokenizer(model, model_id_or_path)

    # Use dummy streamer to ignore other workers' outputs
    def _create_dummy_streamer(self):
        class DummyStreamer:
            def put(self, value):
                pass

            def end(self):
                pass

        return DummyStreamer()

    def _process_config(self, config):
        config["lazy_mode"] = self.use_lazy_mode
        config["hpu_graphs"] = self.use_hpu_graphs
        # max_new_tokens is required for hpu
        if "max_new_tokens" not in config:
            config["max_new_tokens"] = 128

    def get_streamer(self):
        return TextIteratorStreamer(self.tokenizer, skip_prompt=True, timeout=0, skip_special_tokens=True)

    def generate(self, prompt, **config):
        self._process_config(config)

        input_ids, input_length = self.tokenize_inputs(prompt)
        gen_tokens = self.model.generate(input_ids, **config)
        decode_result = self.tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)
        if isinstance(decode_result, list) and len(decode_result) > 1:
            return decode_result
        elif isinstance(decode_result, list) and len(decode_result) == 1:
            decode_result = decode_result[0]
        return GenerateResult(
            text=decode_result,
            input_length=input_length,
            generate_length=gen_tokens.size()[1] - input_length,
        )

    def streaming_generate(self, prompt, streamer, **config):
        self._process_config(config)
        input_ids, _ = self.tokenize_inputs(prompt)
        self.model.generate(
            input_ids,
            streamer=streamer,
            **config,
        )


chat_processor = {
    "ChatModelLlama": ChatModelLLama,
    "ChatModelGptJ": ChatModelGptJ,
    "ChatModelGemma": ChatModelGemma,
    "ChatModelNoFormat": ChatModelNoFormat,
}


# 1: Define a Ray Serve deployment.
@serve.deployment
class LLMServe:
    _DEFAULT_MAX_BATCH_SIZE = 8
    _DEFAULT_MAX_NUM_SEQS = 256

    def __init__(
        self, infer_conf: dict, max_batch_size=_DEFAULT_MAX_BATCH_SIZE, max_num_seqs=_DEFAULT_MAX_NUM_SEQS
    ) -> None:
        # All the initialization code goes here
        self.predictor = HPUPredictor(infer_conf)
        self.loop = asyncio.get_running_loop()
        self.process_tool = chat_processor[infer_conf["chat_processor"]]()
        self.use_openai = False

    def consume_streamer(self, streamer):
        for text in streamer:
            yield text

    async def consume_streamer_async(self, streamer: TextIteratorStreamer):
        while True:
            try:
                for token in streamer:
                    yield token
                break
            except Empty:
                await asyncio.sleep(0.001)

    async def handle_streaming(self, prompt: Union[str, List[str]], config: Dict[str, Any]):
        if isinstance(prompt, List):
            error_message = "Streaming response is not supported when multiple prompts are provided."
            if not self.use_openai:
                yield JSONResponse(
                    status_code=400,
                    content=error_message,
                )
            else:
                yield ModelResponse(
                    error=ErrorResponse(
                        message=error_message,
                        code=400,
                        internal_message=error_message,
                        type="InternalServerError",
                    )
                )
        streamer = self.predictor.get_streamer()
        self.loop.run_in_executor(
            None, functools.partial(self.predictor.streaming_generate, prompt, streamer, **config)
        )

        if not self.use_openai:
            yield StreamingResponse(self.consume_streamer_async(streamer), status_code=200, media_type="text/plain")
        else:
            async for output in self.consume_streamer_async(streamer):
                processed_output = output
                tool_call_list = None
                if self.tools_capture_texts is not None:
                    (processed_output, tool_call_list) = self.tools_capture_texts(
                        output, self.openai_tools_prompter, prompt
                    )
                model_reponse = ModelResponse(
                    generated_text=processed_output,
                    tool_calls=tool_call_list,
                    num_input_tokens=self.predictor.input_length,
                    num_generate_tokens=1,
                    preprocessing_time=0,
                )
                yield model_reponse

    async def handle_non_streaming(self, prompts, config) -> Union[JSONResponse, str]:
        if isinstance(prompts, list):
            return await self.handle_static_batch(prompts, **config)
        return await self.handle_dynamic_batch((prompts, config))

    @serve.batch(max_batch_size=_DEFAULT_MAX_BATCH_SIZE)
    async def handle_dynamic_batch(self, requests):
        batched_prompts: Dict[str, Tuple[Union[str, List[str]]]] = {}
        for i, request in enumerate(requests):
            prompt = request[0]
            config = request[1]
            key = str(dict(sorted(config.items())))
            batched_prompts.setdefault(key, ([], []))
            batched_prompts[key][0].append(prompt)
            batched_prompts[key][1].append(i)

        results = [None] * len(requests)
        for key, (prompts, indices) in batched_prompts.items():
            config = dict(eval(key))
            batched_results = self.predictor.generate(prompts, **config)
            for index, result in zip(indices, batched_results):
                results[index] = result
        if not self.use_openai:
            return results
        else:
            responses = []
            tool_call_list = None
            for result in results:
                if self.tools_capture_texts is not None:
                    result.text, tool_call_list = self.tools_capture_texts.process_full_output(
                        result.text, self.openai_tools_prompter, prompt
                    )
                responses.append(
                    ModelResponse(
                        generated_text=result[-1],
                        tool_calls=tool_call_list,
                        num_input_tokens=self.predictor.input_length,
                        num_generated_tokens=len(result[-1]),
                        preprocessing_time=0,
                    )
                )
            return responses

    async def handle_static_batch(self, prompts: List[str], **config: Dict[str, any]):
        results = self.predictor.generate(prompts, **config)
        if not self.use_openai:
            return results
        else:
            return ModelResponse(
                generated_text=results[0].text,
                num_input_tokens=results[0].input_length,
                num_input_tokens_batch=results[0].input_length,
                num_generated_tokens=results[0].generate_length,
                preprocessing_time=0,
            )

    def preprocess_prompts(self, input: Union[str, List], tools=None, tool_choice=None):
        if isinstance(input, str):
            return input
        elif isinstance(input, List):
            prompts = []
            images = []

            prompt_format = get_prompt_format(input)
            if prompt_format == PromptFormat.CHAT_FORMAT:
                # Process the input prompts with tools
                self.tool_call_list = None
                self.openai_tools_prompter: OpenAIToolsPrompter = OpenAIToolsPrompter() if tools is not None else None
                self.tools_capture_texts: ChatPromptCapture = None
                if self.openai_tools_prompter is not None:
                    input = self.openai_tools_prompter.inject_prompt(input, tools, tool_choice)
                    self.tools_capture_texts = ChatPromptCapture()
                    for m in input:
                        if m.tool_calls is not None:  # type: ignore
                            m.content = self.openai_tools_prompter.content_from_assistant(m)  # type: ignore
                        elif m.tool_call_id is not None:  # type: ignore
                            m.content = self.openai_tools_prompter.content_from_tool(m)  # type: ignore
                # Process the input prompts with MLLM tool
                if self.process_tool is not None:
                    prompt = self.process_tool.get_prompt(input)
                    return prompt
                else:
                    prompts.extend(input)
            elif prompt_format == PromptFormat.PROMPTS_FORMAT:
                prompts.extend(input)
            else:
                raise HTTPException(400, "Invalid prompt format.")
            return prompts
        else:
            raise HTTPException(400, "Invalid prompt format.")

    async def openai_call(self, input: str, config: Dict, streaming_response=True, tools=None, tool_choice=None):
        self.use_openai = True
        prompts = self.preprocess_prompts(input, tools, tool_choice)

        if streaming_response:
            async for result in self.handle_streaming(prompts, config):
                yield result
        else:
            yield await self.handle_non_streaming(prompts, config)
