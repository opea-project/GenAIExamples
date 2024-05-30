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

from typing import Dict

from fastapi import HTTPException
from ray_serve.api_openai_backend.openai_protocol import ModelCard, Prompt
from ray_serve.api_openai_backend.request_handler import handle_request


class RouterQueryClient:
    def __init__(self, serve_deployments):
        self.serve_deployments = serve_deployments

    async def query(self, model: str, prompt: Prompt, request_id: str, streaming_reponse: bool):
        if model in self.serve_deployments:
            deploy_handle = self.serve_deployments[model]
        else:
            raise HTTPException(404, f"Could not find model with id {model}")

        request_config = prompt.parameters
        temperature = request_config.get("temperature", 1.0)
        top_p = request_config.get("top_p", 1.0)
        max_new_tokens = request_config.get("max_tokens", None)
        gen_config = {"max_new_tokens": max_new_tokens, "temperature": temperature, "top_p": top_p}
        if temperature != 1.0 or top_p != 1.0:
            gen_config.update({"do_sample": True})
        if request_config.get("ignore_eos", False):
            gen_config.update({"ignore_eos": True})

        async for x in handle_request(
            model=model,
            prompt=prompt,
            request_id=request_id,
            async_iterator=deploy_handle.options(stream=True)
            .openai_call.options(stream=True, use_new_handle_api=True)
            .remote(
                prompt.prompt,
                gen_config,
                streaming_response=streaming_reponse,
                tools=prompt.tools,
                tool_choice=prompt.tool_choice,
            ),
        ):
            yield x

    async def model(self, model_id: str) -> ModelCard:
        """Get configurations for a supported model."""
        return ModelCard(
            id=model_id,
            root=model_id,
        )

    async def models(self) -> Dict[str, ModelCard]:
        """Get configurations for supported models."""
        metadatas = {}
        for model_id in self.serve_deployments:
            metadatas[model_id] = await self.model(model_id)
        return metadatas
