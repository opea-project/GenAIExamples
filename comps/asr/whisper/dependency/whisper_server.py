# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import os
import uuid
from typing import List, Optional, Union

import uvicorn
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import Response
from pydub import AudioSegment
from starlette.middleware.cors import CORSMiddleware
from whisper_model import WhisperModel

from comps import CustomLogger
from comps.cores.proto.api_protocol import AudioTranscriptionResponse

logger = CustomLogger("whisper")
logflag = os.getenv("LOGFLAG", False)

app = FastAPI()
asr = None

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.get("/v1/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/v1/asr")
async def audio_to_text(request: Request):
    logger.info("Whisper generation begin.")
    uid = str(uuid.uuid4())
    file_name = uid + ".wav"
    request_dict = await request.json()
    audio_b64_str = request_dict.pop("audio")
    with open(file_name, "wb") as f:
        f.write(base64.b64decode(audio_b64_str))

    audio = AudioSegment.from_file(file_name)
    audio = audio.set_frame_rate(16000)

    audio.export(f"{file_name}", format="wav")
    try:
        asr_result = asr.audio2text(file_name)
    except Exception as e:
        logger.error(e)
        asr_result = e
    finally:
        os.remove(file_name)
    return {"asr_result": asr_result}


@app.post("/v1/audio/transcriptions")
async def audio_transcriptions(
    file: UploadFile = File(...),  # Handling the uploaded file directly
    model: str = Form("openai/whisper-small"),
    language: str = Form("english"),
    prompt: str = Form(None),
    response_format: str = Form("json"),
    temperature: float = Form(0),
    timestamp_granularities: List[str] = Form(None),
):
    logger.info("Whisper generation begin.")
    audio_content = await file.read()
    # validate the request parameters
    if model != asr.asr_model_name_or_path:
        raise Exception(
            f"ASR model mismatch! Please make sure you pass --model_name_or_path or set environment variable ASR_MODEL_PATH to {model}"
        )
    asr.language = language
    if prompt is not None or response_format != "json" or temperature != 0 or timestamp_granularities is not None:
        logger.warning(
            "Currently parameters 'language', 'response_format', 'temperature', 'timestamp_granularities' are not supported!"
        )

    uid = str(uuid.uuid4())
    file_name = uid + ".wav"
    # Save the uploaded file
    with open(file_name, "wb") as buffer:
        buffer.write(audio_content)

    audio = AudioSegment.from_file(file_name)
    audio = audio.set_frame_rate(16000)

    audio.export(f"{file_name}", format="wav")

    try:
        asr_result = asr.audio2text(file_name)
    except Exception as e:
        logger.error(e)
        asr_result = e
    finally:
        os.remove(file_name)

    return AudioTranscriptionResponse(text=asr_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7066)
    parser.add_argument("--model_name_or_path", type=str, default="openai/whisper-small")
    parser.add_argument("--language", type=str, default="english")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--return_timestamps", type=str, default=True)

    args = parser.parse_args()
    asr = WhisperModel(
        model_name_or_path=args.model_name_or_path,
        language=args.language,
        device=args.device,
        return_timestamps=args.return_timestamps,
    )

    uvicorn.run(app, host=args.host, port=args.port)
