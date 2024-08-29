# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import base64
import os
import uuid
from functools import partial
from io import BytesIO
from typing import List

import PIL
import PIL.Image
import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from utils import build_logger

from comps.embeddings.multimodal_embeddings.bridgetower import BridgeTowerEmbedding

worker_id = str(uuid.uuid4())[:6]
print(f"worker_id: {worker_id}")
logger = build_logger("embedding_worker", f"bridgetower_embedding_worker_{worker_id}.log")
model_semaphore = None
global_counter = 0

model_name_or_path = None
model_dtype = None
use_hpu_graphs = True


app = FastAPI()


def release_model_semaphore(fn=None):
    model_semaphore.release()
    if fn is not None:
        fn()


def get_queue_length():
    if model_semaphore is None:
        return 0
    else:
        return (
            args.limit_model_concurrency
            - model_semaphore._value
            + (len(model_semaphore._waiters) if model_semaphore._waiters is not None else 0)
        )


def get_status():
    return {
        "model_names": [model_name_or_path],
        "speed": 1,
        "queue_length": get_queue_length(),
        "global_counter": global_counter,
    }


@app.get("/v1/health_check")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200, content=b'{"message" : "BridgeTower server is running..."}')


@app.post("/v1/encode")
async def encode(request: Request) -> Response:
    global model_semaphore, global_counter
    global_counter += 1

    request_dict = await request.json()
    if model_semaphore is None:
        model_semaphore = asyncio.Semaphore(args.limit_model_concurrency)
    await model_semaphore.acquire()

    text = request_dict.pop("text")
    image = None
    if "img_b64_str" in request_dict.keys():
        img_b64_str = request_dict.pop("img_b64_str")
        image = PIL.Image.open(BytesIO(base64.b64decode(img_b64_str)))
    if image is None:
        # embed text only
        embeddings = embedder.embed_documents([text])[0]
    else:
        # embed image and text pair
        embeddings = embedder.embed_image_text_pairs([text], [image], batch_size=1)[0]

    background_tasks = BackgroundTasks()
    background_tasks.add_task(partial(release_model_semaphore))
    return JSONResponse(
        status_code=200,
        content={
            "embedding": embeddings,
        },
        background=background_tasks,
    )


@app.post("/v1/worker_get_status")
async def get_woker_status():
    return get_status()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--model_name_or_path", type=str, default="BridgeTower/bridgetower-large-itm-mlm-itc")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup iterations for benchmarking.")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--limit-model-concurrency", type=int, default=5)

    args = parser.parse_args()
    # get port from env variable if exist
    args.port = int(os.getenv("PORT", 8080))

    print(f"device: {args.device}")
    logger.info(f"args: {args}")

    if args.device == "hpu":
        try:
            import habana_frameworks.torch.core as htcore
        except ImportError:
            print("device: hpu is not available. Using cpu instead!")
            args.device = "cpu"

    model_name_or_path = args.model_name_or_path

    embedder = BridgeTowerEmbedding(device=args.device)

    # warmup
    print("Warmup...")
    image_paths = ["https://llava-vl.github.io/static/images/view.jpg"]
    example_prompts = ["This is test image!"]
    images = []
    for image_path in image_paths:
        images.append(PIL.Image.open(requests.get(image_path, stream=True, timeout=3000).raw))
    for i in range(args.warmup):
        embedder.embed_image_text_pairs(
            example_prompts,
            images,
            batch_size=1,
        )
    print("Done warmup...")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug",
    )
