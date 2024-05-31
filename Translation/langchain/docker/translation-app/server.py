#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import os

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_community.llms import HuggingFaceEndpoint
from prompts import translation_prompt_template
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


short_cut_mapping = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "sv": "Swedish",
    "nl": "Dutch",
    "no": "Norwegian",
    "da": "Danish",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "pl": "Polish",
    "fi": "Finnish",
    "el": "Greek",
    "cs": "Czech",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "ms": "Malay",
    "th": "Thai",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "ro": "Romanian",
    "he": "Hebrew",
    "bn": "Bengali",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "hr": "Croatian",
    "pirate": "Pirate",
    "yoda": "Yoda",
    "minion": "Minion",
}


class TranslationAPIRouter(APIRouter):
    """The router for Language Translation example."""

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

    def handle_translation(self, language_from: str, language_to: str, source_language: str):
        if language_from in short_cut_mapping.keys():
            language_from = short_cut_mapping[language_from]
        if language_to in short_cut_mapping.keys():
            language_to = short_cut_mapping[language_to]
        prompt = self.prompt_template.format(
            language_from=language_from, language_to=language_to, source_language=source_language
        )
        print(f"[translation - nonstream] prompt:{prompt}")
        try:
            response = self.llm(prompt)
            response = {"target_language": response.replace("</s>", "").lstrip()}
        except Exception as e:
            print(f"[translation - nonstream] Error occurred: {e}")
            raise Exception(f"[translation - nonstream] {e}")
        print(f"[translation - nonstream] response:\n{response}")
        return response

    async def handle_translation_stream(self, language_from: str, language_to: str, source_language: str):
        if language_from in short_cut_mapping.keys():
            language_from = short_cut_mapping[language_from]
        if language_to in short_cut_mapping.keys():
            language_to = short_cut_mapping[language_to]
        prompt = self.prompt_template.format(
            language_from=language_from, language_to=language_to, source_language=source_language
        )
        print(f"[translation - stream] prompt:{prompt}")

        async def stream_generator():
            async for chunk in self.llm.astream_log(prompt):
                print(f"[translation - stream] data: {chunk}")
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")


router = TranslationAPIRouter(entrypoint=TGI_ENDPOINT, prompt_template=translation_prompt_template)


@router.post("/v1/translation")
async def translation(request: Request):
    params = await request.json()
    print(f"[translation - nonstream] POST request: /v1/translation, params:{params}")
    language_from = params["language_from"]
    language_to = params["language_to"]
    source_language = params["source_language"]
    try:
        return router.handle_translation(
            language_from=language_from, language_to=language_to, source_language=source_language
        )
    except Exception as e:
        print(f"[translation - nonstream] Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/translation_stream")
async def translation_stream(request: Request):
    params = await request.json()
    print(f"[translation - stream] POST request: /v1/translation_stream, params:{params}")
    language_from = params["language_from"]
    language_to = params["language_to"]
    source_language = params["source_language"]
    try:
        return await router.handle_translation_stream(
            language_from=language_from, language_to=language_to, source_language=source_language
        )
    except Exception as e:
        print(f"[translation - stream] Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(SERVICE_PORT))
