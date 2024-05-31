#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import argparse
import os

import uvicorn
from asr import AudioSpeechRecognition
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from pydub import AudioSegment
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
asr = None

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.get("/v1/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/v1/audio/transcriptions")
async def audio_to_text(file: UploadFile = File(...)):
    file_name = file.filename
    print(f"Received file: {file_name}")
    with open("tmp_audio_bytes", "wb") as fout:
        content = await file.read()
        fout.write(content)
    audio = AudioSegment.from_file("tmp_audio_bytes")
    audio = audio.set_frame_rate(16000)
    # bytes to wav
    file_name = file_name + ".wav"
    audio.export(f"{file_name}", format="wav")
    try:
        asr_result = asr.audio2text(file_name)
    except Exception as e:
        print(e)
        asr_result = e
    finally:
        os.remove(file_name)
        os.remove("tmp_audio_bytes")
    return {"asr_result": asr_result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8008)
    parser.add_argument("--model_name_or_path", type=str, default="openai/whisper-tiny")
    parser.add_argument("--bf16", default=False, action="store_true")
    parser.add_argument("--language", type=str, default="auto")
    parser.add_argument("--device", type=str, default="cpu")

    args = parser.parse_args()
    asr = AudioSpeechRecognition(
        model_name_or_path=args.model_name_or_path, bf16=args.bf16, language=args.language, device=args.device
    )

    uvicorn.run(app, host=args.host, port=args.port)
