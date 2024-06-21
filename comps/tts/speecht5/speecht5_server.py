# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
from io import BytesIO

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response
from speecht5_model import SpeechT5Model
from starlette.middleware.cors import CORSMiddleware

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
    print("SpeechT5 generation begin.")
    request_dict = await request.json()
    text = request_dict.pop("text")

    speech = tts.t2s(text)

    buffered = BytesIO()
    buffered.write(speech.tobytes())
    return {"tts_result": base64.b64encode(buffered.getvalue())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7055)
    parser.add_argument("--device", type=str, default="cpu")

    args = parser.parse_args()
    tts = SpeechT5Model(device=args.device)

    uvicorn.run(app, host=args.host, port=args.port)
