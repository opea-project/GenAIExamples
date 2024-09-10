# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Stand-alone LLaVA FastAPI Server."""

import argparse
import base64
import time
from io import BytesIO

import PIL.Image
import requests
import torch
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from transformers import pipeline

model_name_or_path = None
model_dtype = None
use_hpu_graphs = True

generator = None


app = FastAPI()


def process_image(image, max_len=1344, min_len=672):
    if max(image.size) > max_len:
        max_hw, min_hw = max(image.size), min(image.size)
        aspect_ratio = max_hw / min_hw
        shortest_edge = int(min(max_len / aspect_ratio, min_len, min_hw))
        longest_edge = int(shortest_edge * aspect_ratio)
        W, H = image.size
        if H > W:
            H, W = longest_edge, shortest_edge
        else:
            H, W = shortest_edge, longest_edge
        image = image.resize((W, H))
    return image


@app.get("/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/generate")
async def generate(request: Request) -> Response:  # FIXME batch_size=1 for now, only accept single image
    print("LLaVA generation begin.")
    request_dict = await request.json()
    prompt = request_dict.pop("prompt")
    img_b64_str = request_dict.pop("img_b64_str")
    max_new_tokens = request_dict.pop("max_new_tokens", 100)

    # format the prompt
    prompt = f"<image>\nUSER: {prompt}\nASSISTANT:"

    # Decode and Resize the image
    image = PIL.Image.open(BytesIO(base64.b64decode(img_b64_str)))
    image = process_image(image)

    if args.device == "hpu":
        generate_kwargs = {
            "lazy_mode": True,
            "hpu_graphs": True,
            "max_new_tokens": max_new_tokens,
            "ignore_eos": False,
        }
    else:
        generate_kwargs = {
            "max_new_tokens": max_new_tokens,
        }

    start = time.time()
    result = generator(image, prompt=prompt, batch_size=1, generate_kwargs=generate_kwargs)
    end = time.time()
    result = result[0]["generated_text"].split("ASSISTANT: ")[-1]
    print(f"LLaVA result = {result}, time = {(end-start) * 1000 }ms")
    image.close()
    ret = {"text": result}
    return JSONResponse(ret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8399)
    parser.add_argument("--model_name_or_path", type=str, default="llava-hf/llava-1.5-7b-hf")
    parser.add_argument("--use_hpu_graphs", default=False, action="store_true")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup iterations for benchmarking.")
    parser.add_argument("--device", type=str, default="hpu")
    parser.add_argument("--bf16", default=True, action="store_true")

    args = parser.parse_args()
    print(f"device: {args.device}")
    if args.device == "hpu":
        from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

        adapt_transformers_to_gaudi()

    if args.bf16:
        model_dtype = torch.bfloat16
    else:
        model_dtype = torch.float32

    model_name_or_path = args.model_name_or_path

    generator = pipeline(
        "image-to-text",
        model=args.model_name_or_path,
        torch_dtype=model_dtype,
        device=args.device,
    )

    # warmup
    print("LLaVA warmup...")
    if args.device == "hpu":
        generate_kwargs = {
            "lazy_mode": True,
            "hpu_graphs": True,
            "max_new_tokens": 128,
            "ignore_eos": False,
        }
    else:
        generate_kwargs = {
            "max_new_tokens": 128,
        }

    if args.device == "hpu" and args.use_hpu_graphs:
        from habana_frameworks.torch.hpu import wrap_in_hpu_graph

        generator.model = wrap_in_hpu_graph(generator.model)

    image_paths = ["https://llava-vl.github.io/static/images/view.jpg"]
    images = []
    for image_path in image_paths:
        images.append(PIL.Image.open(requests.get(image_path, stream=True, timeout=3000).raw))
    for i in range(args.warmup):
        generator(
            images,
            prompt="<image>\nUSER: What's the content of the image?\nASSISTANT:",
            batch_size=1,
            generate_kwargs=generate_kwargs,
        )

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug",
    )
