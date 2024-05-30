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

import os
import uuid
from typing import AsyncGenerator, List

import async_timeout
from fastapi import FastAPI
from fastapi import Response as FastAPIResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from ray_serve.api_openai_backend.openai_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    CompletionResponseChoice,
    DeltaChoices,
    DeltaContent,
    DeltaEOS,
    DeltaRole,
    ModelCard,
    ModelList,
    ModelResponse,
    Prompt,
    UsageInfo,
)
from ray_serve.api_openai_backend.query_client import RouterQueryClient
from ray_serve.api_openai_backend.request_handler import OpenAIHTTPException, openai_exception_handler
from starlette.responses import Response, StreamingResponse

# timeout in 10 minutes. Streaming can take longer than 3 min
TIMEOUT = float(os.environ.get("ROUTER_HTTP_TIMEOUT", 1800))


def init() -> FastAPI:
    router_app = FastAPI()
    router_app.add_exception_handler(OpenAIHTTPException, openai_exception_handler)
    router_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return router_app


router_app = init()


async def _completions_wrapper(
    completion_id: str,
    body: CompletionRequest,
    response: Response,
    generator: AsyncGenerator[ModelResponse, None],
) -> AsyncGenerator[str, None]:
    had_error = False
    async with async_timeout.timeout(TIMEOUT):
        all_results = []
        async for results in generator:
            for subresult in results.unpack():
                all_results.append(subresult)
                subresult_dict = subresult.dict()
                if subresult_dict.get("error"):
                    response.status_code = subresult_dict["error"]["code"]
                    # Drop finish reason as OpenAI doesn't expect it
                    # for errors in streaming
                    subresult_dict["finish_reason"] = None
                    all_results.pop()
                    had_error = True
                    yield "data: " + ModelResponse(**subresult_dict).json() + "\n\n"
                    # Return early in case of an error
                    break
                choices = [
                    CompletionResponseChoice(
                        index=0,
                        text=subresult_dict["generated_text"] or "",
                        finish_reason=subresult_dict["finish_reason"],
                    )
                ]
                usage = None
                yield "data: " + CompletionResponse(
                    id=completion_id,
                    object="text_completion",
                    model=body.model,
                    choices=choices,
                    usage=usage,
                ).json() + "\n\n"
            if had_error:
                # Return early in case of an error
                break
        if not had_error:
            usage = UsageInfo.from_response(ModelResponse.merge_stream(*all_results)) if all_results else None
            yield "data: " + CompletionResponse(
                id=completion_id,
                object="text_completion",
                model=body.model,
                choices=choices,
                usage=usage,
            ).json() + "\n\n"
        yield "data: [DONE]\n\n"


async def _chat_completions_wrapper(
    completion_id: str,
    body: ChatCompletionRequest,
    response: Response,
    generator: AsyncGenerator[ModelResponse, None],
) -> AsyncGenerator[str, None]:
    had_error = False
    async with async_timeout.timeout(TIMEOUT):
        finish_reason = None
        choices: List[DeltaChoices] = [
            DeltaChoices(
                delta=DeltaRole(role="assistant"),
                index=0,
                finish_reason=None,
            )
        ]
        chunk = ChatCompletionResponse(
            id=completion_id,
            object="chat.completion.chunk",
            model=body.model,
            choices=choices,
            usage=None,
        )
        data = chunk.json()
        yield f"data: {data}\n\n"

        all_results = []
        async for results in generator:
            for subresult in results.unpack():
                all_results.append(subresult)
                subresult_dict = subresult.dict()
                if subresult_dict.get("error"):
                    response.status_code = subresult_dict["error"]["code"]
                    # Drop finish reason as OpenAI doesn't expect it
                    # for errors in streaming
                    subresult_dict["finish_reason"] = None
                    all_results.pop()
                    had_error = True
                    yield "data: " + ModelResponse(**subresult_dict).json() + "\n\n"
                    # Return early in case of an error
                    break
                else:
                    finish_reason = subresult_dict["finish_reason"]
                    choices = [
                        DeltaChoices(
                            delta=DeltaContent(
                                content=subresult_dict["generated_text"] or "",
                                tool_calls=subresult_dict["tool_calls"] or None,
                            ),
                            index=0,
                            finish_reason=None,
                        )
                    ]
                    chunk = ChatCompletionResponse(
                        id=completion_id,
                        object="chat.completion.chunk",
                        model=body.model,
                        choices=choices,
                        usage=None,
                    )
                    # data = chunk.json(exclude_unset=True, ensure_ascii=False)
                    data = chunk.json()
                    yield f"data: {data}\n\n"
            if had_error:
                # Return early in case of an error
                break
        if not had_error:
            choices = [
                DeltaChoices(
                    delta=DeltaEOS(),
                    index=0,
                    finish_reason=finish_reason,
                )
            ]
            usage = UsageInfo.from_response(ModelResponse.merge_stream(*all_results)) if all_results else None
            chunk = ChatCompletionResponse(
                id=completion_id,
                object="chat.completion.result",
                model=body.model,
                choices=choices,
                usage=usage,
            )
            data = chunk.json()
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"


class Router:
    def __init__(
        self,
        query_client: RouterQueryClient,
    ) -> None:
        self.query_client = query_client

    @router_app.get("/v1/models", response_model=ModelList)
    async def models(self) -> ModelList:
        """OpenAI API-compliant endpoint to get all models."""
        models = await self.query_client.models()
        return ModelList(data=list(models.values()))

    # :path allows us to have slashes in the model name
    @router_app.get("/v1/models/{model:path}", response_model=ModelCard)
    async def model_data(self, model: str) -> ModelCard:
        """OpenAI API-compliant endpoint to get one model.

        :param model: The model ID (e.g. "amazon/LightGPT")
        """
        model = model.replace("--", "/")
        model_data = await self.query_client.model(model)
        if model_data is None:
            raise OpenAIHTTPException(
                message=f"Invalid model '{model}'",
                status_code=status.HTTP_400_BAD_REQUEST,
                type="InvalidModel",
            )
        return model_data

    @router_app.post("/v1/completions")
    async def completions(
        self,
        body: CompletionRequest,
        response: FastAPIResponse,
    ):
        """Given a prompt, the model will return one or more predicted completions,
        and can also return the probabilities of alternative tokens at each position.

        Returns:
            A response object with completions.
        """
        prompt = Prompt(
            prompt=body.prompt,
            parameters=dict(body),
            use_prompt_format=False,
        )
        request_id = f"cmpl-{str(uuid.uuid4().hex)}"

        if body.stream:
            return StreamingResponse(
                _completions_wrapper(
                    request_id,
                    body,
                    response,
                    self.query_client.query(body.model, prompt, request_id, body.stream),
                ),
                media_type="text/event-stream",
            )
        else:
            async with async_timeout.timeout(TIMEOUT):
                results_reponse = self.query_client.query(body.model, prompt, request_id, body.stream)
                async for results in results_reponse:
                    if results.error:
                        raise OpenAIHTTPException(
                            message=results.error.message,
                            status_code=results.error.code,
                            type=results.error.type,
                        )
                    results = results.dict()

                    choices = [
                        CompletionResponseChoice(
                            index=0,
                            text=results["generated_text"] or "",
                            finish_reason=results["finish_reason"],
                        )
                    ]
                    usage = UsageInfo.from_response(results)

                    return CompletionResponse(
                        id=request_id,
                        object="text_completion",
                        model=body.model,
                        choices=choices,
                        usage=usage,
                    )

    @router_app.post("/v1/chat/completions")
    async def chat(
        self,
        body: ChatCompletionRequest,
        response: FastAPIResponse,
    ):
        """Given a prompt, the model will return one or more predicted completions,
        and can also return the probabilities of alternative tokens at each position.

        Returns:
            A response object with completions.
        """
        prompt = Prompt(
            prompt=body.messages,
            parameters=dict(body),
            tools=body.tools,
            tool_choice=body.tool_choice,
        )
        request_id = f"chatcmpl-{str(uuid.uuid4().hex)}"
        if body.stream:
            return StreamingResponse(
                _chat_completions_wrapper(
                    request_id,
                    body,
                    response,
                    self.query_client.query(body.model, prompt, request_id, body.stream),
                ),
                media_type="text/event-stream",
            )
        else:
            async with async_timeout.timeout(TIMEOUT):
                results_reponse = self.query_client.query(body.model, prompt, request_id, body.stream)
                async for results in results_reponse:
                    if results.error:
                        raise OpenAIHTTPException(
                            message=results.error.message,
                            status_code=results.error.code,
                            type=results.error.type,
                        )

                    if results.tool_calls is not None:
                        msg = ChatMessage(role="assistant", tool_calls=results.tool_calls)
                        # deleting this fields so that they don't appear in the response
                        del msg.tool_call_id
                    else:
                        msg = ChatMessage(role="assistant", content=results.generated_text or "")

                    usage = UsageInfo.from_response(results.dict())
                    return ChatCompletionResponse(
                        id=request_id,
                        object="chat.completion",
                        model=body.model,
                        choices=[
                            ChatCompletionResponseChoice(
                                index=0,
                                message=msg,
                                finish_reason=results.finish_reason,
                            )
                        ],
                        usage=usage,
                    )

    @router_app.get("/v1/health_check")
    async def health_check(self) -> bool:
        """Check if the routher is still running."""
        return True
