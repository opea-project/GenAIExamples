#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Mapping, Optional

import requests
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
from langchain_core.pydantic_v1 import root_validator
from langchain_core.utils import get_pydantic_field_names

logger = logging.getLogger(__name__)

VALID_TASKS = (
    "text2text-generation",
    "text-generation",
    "summarization",
    "conversational",
)


class NeuralChatEndpoint(LLM):
    """NeuralChat Endpoint.
    To leverage the endpoint of NeuralChat which support Tensor Parallelism for LLM inferencing.

    Example:
        .. code-block:: python

            # Streaming response example
            from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

            callbacks = [StreamingStdOutCallbackHandler()]
            llm = NeuralChatEndpoint(
                endpoint_url="http://localhost:8010/",
                max_new_tokens=512,
                top_k=10,
                top_p=0.95,
                typical_p=0.95,
                temperature=0.01,
                repetition_penalty=1.03,
                streaming=True,
            )
            print(llm("What is Deep Learning?"))
    """  # noqa: E501

    endpoint_url: Optional[str] = None
    """Endpoint URL to use."""
    max_new_tokens: int = 512
    """Maximum number of generated tokens."""
    top_k: Optional[int] = 1
    """The number of highest probability vocabulary tokens to keep for
    top-k-filtering."""
    top_p: Optional[float] = 1.0
    """If set to < 1, only the smallest set of most probable tokens with probabilities
    that add up to `top_p` or higher are kept for generation."""
    temperature: Optional[float] = 0.7
    """The value used to module the logits distribution."""
    repetition_penalty: Optional[float] = 1.0
    """The parameter for repetition penalty.

    1.0 means no penalty.
    See [this paper](https://arxiv.org/pdf/1909.05858.pdf) for more details.
    """
    timeout: int = 120
    """Timeout in seconds."""
    streaming: bool = False
    """Whether to generate a stream of tokens asynchronously."""
    task: Optional[str] = None
    """Task to call the model with.

    Should be a task that returns `generated_text` or `summary_text`.
    """

    @root_validator(pre=True)
    def build_extra(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Build extra kwargs from additional params that were passed in."""
        all_required_field_names = get_pydantic_field_names(cls)
        extra = values.get("model_kwargs", {})
        for field_name in list(values):
            if field_name in extra:
                raise ValueError(f"Found {field_name} supplied twice.")
            if field_name not in all_required_field_names:
                logger.warning(
                    f"""WARNING! {field_name} is not default parameter.
                    {field_name} was transferred to model_kwargs.
                    Please make sure that {field_name} is what you intended."""
                )
                extra[field_name] = values.pop(field_name)

        invalid_model_kwargs = all_required_field_names.intersection(extra.keys())
        if invalid_model_kwargs:
            raise ValueError(
                f"Parameters {invalid_model_kwargs} should be specified explicitly. "
                f"Instead they were passed in as part of `model_kwargs` parameter."
            )

        values["model_kwargs"] = extra
        if "endpoint_url" not in values:
            raise ValueError("Please specify an `endpoint_url` for the model.")
        values["model"] = values.get("endpoint_url")
        return values

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for calling text generation inference API."""
        return {
            "max_new_tokens": self.max_new_tokens,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "repetition_penalty": self.repetition_penalty,
        }

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        _model_kwargs = {}
        return {
            **{"endpoint_url": self.endpoint_url, "task": self.task},
            **{"model_kwargs": _model_kwargs},
        }

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "neuralchat_endpoint"

    def _invocation_params(self, runtime_stop: Optional[List[str]], **kwargs: Any) -> Dict[str, Any]:
        params = {**self._default_params, **kwargs}
        # params["stop_sequences"] = params["stop_sequences"] + (runtime_stop or [])
        return params

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call out to NeuralChat's inference endpoint."""
        pass

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        pass

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        invocation_params = self._invocation_params(stop, **kwargs)
        endpoint_url = self.endpoint_url
        data = {
            "messages": prompt,
            "model": "Intel/neural-chat-7b-v3-1",
            "stream": True,
            "max_tokens": invocation_params["max_new_tokens"],
        }

        response = requests.post(endpoint_url, json=data, stream=True)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line != "data: [DONE]":
                        json_res = json.loads(decoded_line[6:])
                        delta = json_res["choices"][0]["delta"]
                        if "content" in delta.keys():
                            text = delta["content"]
                            chunk = GenerationChunk(text=text)
                            yield chunk
                            if run_manager:
                                run_manager.on_llm_new_token(chunk.text)
        else:
            print(f"fail to call {endpoint_url}: {response.status_code}")

    async def _astream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        invocation_params = self._invocation_params(stop, **kwargs)
        endpoint_url = self.endpoint_url
        data = {
            "messages": prompt,
            "model": "Intel/neural-chat-7b-v3-1",
            "stream": True,
            "max_tokens": invocation_params["max_new_tokens"],
        }

        response = requests.post(endpoint_url, json=data, stream=True)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line != "data: [DONE]":
                        json_res = json.loads(decoded_line[6:])
                        delta = json_res["choices"][0]["delta"]
                        if "content" in delta.keys():
                            text = delta["content"]
                            chunk = GenerationChunk(text=text)
                            yield chunk
                            if run_manager:
                                run_manager.on_llm_new_token(chunk.text)
        else:
            print(f"fail to call {endpoint_url}: {response.status_code}")
