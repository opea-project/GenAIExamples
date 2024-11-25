# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import os

import soundfile as sf
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
from speecht5_model import SpeechT5Model
from starlette.middleware.cors import CORSMiddleware

from comps import CustomLogger
from comps.cores.proto.api_protocol import AudioSpeechRequest

logger = CustomLogger("speecht5")
logflag = os.getenv("LOGFLAG", False)

app = FastAPI()
tts = None

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.get("/v1/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/v1/tts")
async def text_to_speech(request: Request):
    logger.info("SpeechT5 generation begin.")
    request_dict = await request.json()
    text = request_dict.pop("text")

    speech = tts.t2s(text)
    sf.write("tmp.wav", speech, samplerate=16000)
    with open("tmp.wav", "rb") as f:
        bytes = f.read()
    b64_str = base64.b64encode(bytes).decode()

    return {"tts_result": b64_str}


@app.post("/v1/audio/speech")
async def audio_speech(request: AudioSpeechRequest):
    logger.info("SpeechT5 generation begin.")
    # validate the request parameters
    if request.model != tts.model_name_or_path:
        raise Exception("TTS model mismatch! Currently only support model: microsoft/speecht5_tts")
    if request.voice not in ["default", "male"] or request.speed != 1.0:
        logger.warning("Currently parameter 'speed' can only be 1.0 and 'voice' can only be default or male!")

    speech = tts.t2s(request.input, voice=request.voice)

    tmp_path = "tmp.wav"
    sf.write(tmp_path, speech, samplerate=16000)

    def audio_gen():
        with open(tmp_path, "rb") as f:
            yield from f

    return StreamingResponse(audio_gen(), media_type=f"audio/{request.response_format}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7055)
    parser.add_argument("--device", type=str, default="cpu")

    args = parser.parse_args()
    tts = SpeechT5Model(device=args.device)

    uvicorn.run(app, host=args.host, port=args.port)
