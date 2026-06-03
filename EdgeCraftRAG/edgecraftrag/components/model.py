# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import io
import os
from pathlib import Path
import asyncio
from typing import Any, Optional
import openvino_genai
import openvino as ov
import numpy as np
from edgecraftrag.base import BaseComponent, CompType, ModelType
from llama_index.embeddings.huggingface_openvino import OpenVINOEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openvino import OpenVINOLLM
from llama_index.postprocessor.openvino_rerank import OpenVINORerank
from edgecraftrag.components.ov_llamaindex_helper import OpenVINOGenAIEmbedding, OpenVINOGenAIReranking
from llama_index.llms.openvino_genai import OpenVINOGenAILLM
from pydantic import Field, model_serializer
from llama_index.core.base.llms.types import CompletionResponse, CompletionResponseAsyncGen, CompletionResponseGen
from threading import Event, Thread

def resolve_model_path(model_path: str) -> str:
    if not model_path:
        return model_path

    path_obj = Path(model_path)
    if path_obj.is_absolute() and path_obj.exists():
        return str(path_obj)

    candidates = [
        Path.cwd() / path_obj,
        Path(__file__).resolve().parents[2] / path_obj,
        Path(__file__).resolve().parents[3] / path_obj,
    ]

    model_env = os.getenv("MODEL_PATH")
    container_model_root = Path("/home/user/models")
    if model_env:
        model_root = Path(model_env).expanduser().resolve()
        model_parts = list(path_obj.parts)
        if model_parts[:1] == ["."]:
            model_parts = model_parts[1:]
        if model_parts[:1] == ["models"]:
            model_parts = model_parts[1:]
        if model_parts:
            candidates.append(model_root / Path(*model_parts))
            candidates.append(model_root / path_obj.name)

    model_parts = list(path_obj.parts)
    if model_parts[:1] == ["."]:
        model_parts = model_parts[1:]
    if model_parts[:1] == ["models"]:
        model_parts = model_parts[1:]
    if model_parts:
        candidates.append(container_model_root / Path(*model_parts))
        candidates.append(container_model_root / path_obj.name)

    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            continue
        if resolved.exists():
            return str(resolved)

    return model_path


def model_exist(model_path):
    model_path = resolve_model_path(model_path)
    model_dir = Path(model_path)
    return (
        model_dir.is_dir()
        and (model_dir / "openvino_model.xml").exists()
        and (model_dir / "openvino_model.bin").exists()
    )


class BaseModelComponent(BaseComponent):

    model_id: Optional[str] = Field(default="")
    model_path: Optional[str] = Field(default="")
    weight: Optional[str] = Field(default="")
    device: Optional[str] = Field(default="cpu")
    api_base: Optional[str] = Field(default=None)

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "type": self.comp_subtype,
            "model_id": self.model_id,
            "model_path": self.model_path,
            "weight": self.weight,
            "device": self.device,
            "api_base": self.api_base,
        }
        return set


class OpenAIEmbeddingModel(BaseModelComponent, OpenAIEmbedding):
    def __init__(self, model_id, api_base, **kwargs):
        api_base = api_base + "/v1" if api_base and not api_base.endswith("/v1") else api_base
        super().__init__(
            model_id=model_id,
            api_base=api_base,
            **kwargs,
        )
        OpenAIEmbedding.__init__(
            self, model_id_or_path=model_id, model_name=model_id, api_base=api_base, api_key="unused"
        )
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.VLLM_EMBEDDING
        self.model_id = model_id
        self.model_path = "unused"
        self.device = "unused"
        self.weight = ""


class OpenVINOEmbeddingModel(BaseModelComponent, OpenVINOEmbedding):

    def __init__(self, model_id, model_path, device, weight):
        model_path = resolve_model_path(model_path)
        if not model_exist(model_path):
            OpenVINOEmbedding.create_and_save_openvino_model(model_id, model_path)
        model_kwargs={
            "ov_config": {
                "NUM_STREAMS": "1",
                "PERFORMANCE_HINT": "LATENCY"
            }
        }
        OpenVINOEmbedding.__init__(self, model_id_or_path=model_path, device=device, model_kwargs=model_kwargs)
        if device == "AUTO":
            real_device=self._model.request.get_property("EXECUTION_DEVICES")[0]
            self._model.to(real_device)
            self._model.compile()
            device=real_device
        buf = io.BytesIO()
        self._model.request.export_model(buf)
        self.size_mb = len(buf.getvalue()) / 1024 / 1024
        buf.seek(0)
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.EMBEDDING
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = ""

class OpenVINOGenAIEmbeddingModel(BaseModelComponent, OpenVINOGenAIEmbedding):

    def __init__(self, model_id, model_path, device, weight):
        max_length=512
        model_path = resolve_model_path(model_path)
        if not model_exist(model_path):
            OpenVINOGenAIEmbedding.create_and_save_openvino_model(model_id, model_path)
        if device == "NPU":
            OpenVINOGenAIEmbedding.__init__(self, model_path=model_path, device=device, embed_batch_size=1, pad_to_max_length=True, max_length=512, normalize=True, pooling="mean", padding_side="right")
        else:
            OpenVINOGenAIEmbedding.__init__(self, model_path=model_path, device=device, pad_to_max_length=True, max_length=max_length, normalize=True, pooling="mean", padding_side="right")
        self.size_mb = round(os.path.getsize(model_path+"/openvino_model.bin")/(1024*1024),3)
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.EMBEDDING
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = ""
        self.model_id_or_path = model_path

class OpenVINORerankModel(BaseModelComponent, OpenVINORerank):

    def __init__(self, model_id, model_path, device, weight):
        model_path = resolve_model_path(model_path)
        if not model_exist(model_path):
            OpenVINORerank.create_and_save_openvino_model(model_id, model_path)
        model_kwargs={
            "ov_config": {
                "NUM_STREAMS": "1",
                "PERFORMANCE_HINT": "LATENCY"
            }
        }

        OpenVINORerank.__init__(
            self,
            model_id_or_path=model_path,
            device=device,
            model_kwargs=model_kwargs
        )
        if device == "AUTO":
            real_device=self._model.request.get_property("EXECUTION_DEVICES")[0]
            self._model.to(real_device)
            self._model.compile()
            device=real_device
        buf = io.BytesIO()
        self._model.request.export_model(buf)
        self.size_mb = len(buf.getvalue()) / 1024 / 1024
        buf.seek(0)
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.RERANKER
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = ""

class OpenVINOGenAIRerankModel(BaseModelComponent, OpenVINOGenAIReranking):

    def __init__(self, model_id, model_path, device, weight):
        max_length=512
        model_path = resolve_model_path(model_path)
        if not model_exist(model_path):
            OpenVINOGenAIReranking.create_and_save_openvino_model(model_id, model_path)
        OpenVINOGenAIReranking.__init__(
            self,
            model_id_or_path=model_path,
            device=device,
            max_length=max_length,
            pad_to_max_length=True,  
            padding_side="right"
        )
        self.size_mb = round(os.path.getsize(model_path+"/openvino_model.bin")/(1024*1024),3)
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.RERANKER
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = ""


class OpenVINOLLMModel(BaseModelComponent, OpenVINOLLM):

    def __init__(self, model_id, model_path, device, weight, model=None):
        model_path = resolve_model_path(model_path)
        OpenVINOLLM.__init__(
            self,
            model_id_or_path=model_path,
            model=model,
            device_map=device,
        )
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.LLM
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = weight

class OpenVINOGenAILLMModel(BaseModelComponent, OpenVINOGenAILLM):

    def __init__(self, model_id, model_path, device, weight, model=None):
        model_path = resolve_model_path(model_path)
        OpenVINOGenAILLM.__init__(
            self,
            model_path=model_path,
            device=device,
        )
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.LLM
        self.model_id = model_id
        self.model_path = model_path
        self.perf_metrics = None
        self.device = device
        self.weight = weight
        self.model_name = model_id
        self.device_map = device
        self._model = self._pipe

    

    

    async def astream_complete_with_bench(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        async def gen() -> CompletionResponseAsyncGen:
            loop = asyncio.get_running_loop()
            message_queue: asyncio.Queue[Optional[CompletionResponse]] = asyncio.Queue()
            error_holder = {}

            def worker() -> None:
                try:
                    for message in self.stream_complete_with_bench(prompt, formatted=formatted, **kwargs):
                        asyncio.run_coroutine_threadsafe(message_queue.put(message), loop).result()
                except Exception as exc:
                    error_holder["error"] = exc
                finally:
                    asyncio.run_coroutine_threadsafe(message_queue.put(None), loop).result()

            worker_thread = Thread(target=worker, daemon=True)
            worker_thread.start()

            while True:
                message = await message_queue.get()
                if message is None:
                    break
                yield message

            if "error" in error_holder:
                raise error_holder["error"]
        
        return gen()

    def stream_complete_with_bench(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        """Streaming completion endpoint."""
        full_prompt = prompt
        if not formatted:
            if self.query_wrapper_prompt:
                full_prompt = self.query_wrapper_prompt.format(query_str=prompt)
            if self.system_prompt:
                full_prompt = f"{self.system_prompt} {full_prompt}"

        input_data = self._tokenizer.encode(full_prompt)
        input_ids =  input_data.input_ids.data
        attention_mask = input_data.attention_mask
        full_prompt = openvino_genai.TokenizedInputs(ov.Tensor(input_ids), attention_mask)
        generation_holder = {}
        error_holder = {}

        def run_generation() -> None:
            try:
                generation_holder["result"] = self._pipe.generate(
                    full_prompt,
                    self.config,
                    streamer=self._streamer,
                    **kwargs
                )
            except Exception as exc:
                error_holder["error"] = exc

        def gen() -> CompletionResponseGen:
            generation_thread = Thread(target=run_generation, daemon=True)
            generation_thread.start()

            text = ""
            for token in self._streamer:
                text += token
                yield CompletionResponse(text=text, delta=token)

            generation_thread.join()

            if "error" in error_holder:
                raise error_holder["error"]

            generation_result = generation_holder.get("result")
            if generation_result is not None:
                self.perf_metrics = generation_result.perf_metrics

        return gen()


    def complete_with_bench(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        """Completion endpoint."""
        full_prompt = prompt
        if not formatted:
            if self.query_wrapper_prompt:
                full_prompt = self.query_wrapper_prompt.format(query_str=prompt)
            if self.completion_to_prompt:
                full_prompt = self.completion_to_prompt(full_prompt)
            elif self.system_prompt:
                full_prompt = f"{self.system_prompt} {full_prompt}"

        
        input_data = self._tokenizer.encode(full_prompt)
        input_ids =  input_data.input_ids.data
        attention_mask = input_data.attention_mask
        full_prompt = openvino_genai.TokenizedInputs(ov.Tensor(input_ids), attention_mask)
        generation_result = self._pipe.generate(full_prompt, self.config, **kwargs)
        self.perf_metrics = generation_result.perf_metrics
        generated_tokens = np.array(generation_result.tokens)
        completion = self._tokenizer.decode(generated_tokens)
        token = completion[0] 
        return CompletionResponse(text=token, raw={"model_output": token})