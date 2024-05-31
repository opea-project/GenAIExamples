#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import os
from typing import Optional

from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.pydantic_v1 import BaseModel
from openai_protocol import ChatCompletionRequest, ChatCompletionResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


def filter_code_format(code):
    language_prefixes = {
        "go": "```go",
        "c": "```c",
        "cpp": "```cpp",
        "java": "```java",
        "python": "```python",
        "typescript": "```typescript",
    }
    suffix = "\n```"

    # Find the first occurrence of a language prefix
    first_prefix_pos = len(code)
    for prefix in language_prefixes.values():
        pos = code.find(prefix)
        if pos != -1 and pos < first_prefix_pos:
            first_prefix_pos = pos + len(prefix) + 1

    # Find the first occurrence of the suffix after the first language prefix
    first_suffix_pos = code.find(suffix, first_prefix_pos + 1)

    # Extract the code block
    if first_prefix_pos != -1 and first_suffix_pos != -1:
        return code[first_prefix_pos:first_suffix_pos]
    elif first_prefix_pos != -1:
        return code[first_prefix_pos:]

    return code


class CodeGenAPIRouter(APIRouter):
    def __init__(self, entrypoint) -> None:
        super().__init__()
        self.entrypoint = entrypoint
        print(f"[codegen - router] Initializing API Router, entrypoint={entrypoint}")

        # Define LLM
        callbacks = [StreamingStdOutCallbackHandler()]
        self.llm = HuggingFaceEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
            callbacks=callbacks,
        )
        print("[codegen - router] LLM initialized.")

    def handle_chat_completion_request(self, request: ChatCompletionRequest):
        try:
            print(f"Predicting chat completion using prompt '{request.prompt}'")
            if request.stream:

                async def stream_generator():
                    for chunk in self.llm.stream(request.prompt):
                        yield f"data: {chunk.encode()}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")
            else:
                result = self.llm(request.prompt)
                response = filter_code_format(result)
        except Exception as e:
            print(f"An error occurred: {e}")
        else:
            print("Chat completion finished.")
            return ChatCompletionResponse(response=response)


tgi_endpoint = os.getenv("TGI_ENDPOINT", "http://localhost:8080")
router = CodeGenAPIRouter(tgi_endpoint)


def check_completion_request(request: BaseModel) -> Optional[str]:
    if request.temperature is not None and request.temperature < 0:
        return f"Param Error: {request.temperature} is less than the minimum of 0 --- 'temperature'"

    if request.temperature is not None and request.temperature > 2:
        return f"Param Error: {request.temperature} is greater than the maximum of 2 --- 'temperature'"

    if request.top_p is not None and request.top_p < 0:
        return f"Param Error: {request.top_p} is less than the minimum of 0 --- 'top_p'"

    if request.top_p is not None and request.top_p > 1:
        return f"Param Error: {request.top_p} is greater than the maximum of 1 --- 'top_p'"

    if request.top_k is not None and (not isinstance(request.top_k, int)):
        return f"Param Error: {request.top_k} is not valid under any of the given schemas --- 'top_k'"

    if request.top_k is not None and request.top_k < 1:
        return f"Param Error: {request.top_k} is greater than the minimum of 1 --- 'top_k'"

    if request.max_new_tokens is not None and (not isinstance(request.max_new_tokens, int)):
        return f"Param Error: {request.max_new_tokens} is not valid under any of the given schemas --- 'max_new_tokens'"

    return None


# router /v1/code_generation only supports non-streaming mode.
@router.post("/v1/code_generation")
async def code_generation_endpoint(chat_request: ChatCompletionRequest):
    ret = check_completion_request(chat_request)
    if ret is not None:
        raise RuntimeError("Invalid parameter.")
    return router.handle_chat_completion_request(chat_request)


# router /v1/code_chat supports both non-streaming and streaming mode.
@router.post("/v1/code_chat")
async def code_chat_endpoint(chat_request: ChatCompletionRequest):
    ret = check_completion_request(chat_request)
    if ret is not None:
        raise RuntimeError("Invalid parameter.")
    return router.handle_chat_completion_request(chat_request)


app.include_router(router)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
