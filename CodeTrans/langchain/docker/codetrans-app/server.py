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

import os

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_community.llms import HuggingFaceEndpoint
from prompts import codetrans_prompt_template
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TGI_ENDPOINT = os.getenv("TGI_ENDPOINT", "http://localhost:8080")
SERVICE_PORT = os.getenv("SERVER_PORT", 8000)


class CodeTranslationAPIRouter(APIRouter):
    """The router for CodeTranslation example."""

    def __init__(self, entrypoint: str, prompt_template: str) -> None:
        super().__init__()
        self.entrypoint = entrypoint

        # setup TGI endpoint
        self.llm = HuggingFaceEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
        )

        self.prompt_template = prompt_template

    def handle_code_translation(self, language_from: str, language_to: str, source_code: str):
        prompt = self.prompt_template.format(
            language_from=language_from, language_to=language_to, source_code=source_code
        )
        print(f"[codetrans - nonstream] prompt:{prompt}")
        try:
            response = self.llm(prompt)
        except Exception as e:
            print(f"[codetrans - nonstream] Error occurred: {e}")
            raise Exception(f"[codetrans - nonstream] {e}")
        print(f"[codetrans - nonstream] response:\n{response}")
        return response

    async def handle_code_translation_stream(self, language_from: str, language_to: str, source_code: str):
        prompt = self.prompt_template.format(
            language_from=language_from, language_to=language_to, source_code=source_code
        )
        print(f"[codetrans - stream] prompt:{prompt}")

        async def stream_generator():
            for chunk in self.llm.stream(prompt):
                chunk_repr = repr(chunk.encode("utf-8"))
                print(f"[codetrans - stream] data: {chunk_repr}")
                yield f"data: {chunk_repr}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")


router = CodeTranslationAPIRouter(entrypoint=TGI_ENDPOINT, prompt_template=codetrans_prompt_template)


@router.post("/v1/code_translation")
async def code_translation(request: Request):
    params = await request.json()
    print(f"[codetrans - nonstream] POST request: /v1/code_translation, params:{params}")
    language_from = params["language_from"]
    language_to = params["language_to"]
    source_code = params["source_code"]
    try:
        return router.handle_code_translation(
            language_from=language_from, language_to=language_to, source_code=source_code
        )
    except Exception as e:
        print(f"[codetrans - nonstream] Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/code_translation_stream")
async def code_translation_stream(request: Request):
    params = await request.json()
    print(f"[codetrans - stream] POST request: /v1/code_translation_stream, params:{params}")
    language_from = params["language_from"]
    language_to = params["language_to"]
    source_code = params["source_code"]
    try:
        return await router.handle_code_translation_stream(
            language_from=language_from, language_to=language_to, source_code=source_code
        )
    except Exception as e:
        print(f"[codetrans - stream] Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(SERVICE_PORT))
