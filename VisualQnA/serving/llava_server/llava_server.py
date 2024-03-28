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
from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi
from transformers import pipeline

model_name_or_path = None
model_dtype = None
use_hpu_graphs = True

generator = None

app = FastAPI()


@app.get("/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/generate")
async def generate(request: Request) -> Response:  # FIXME batch_size=1 for now, only accept single image
    request_dict = await request.json()
    prompt = request_dict.pop("prompt")
    # image_path = request_dict.pop("image_path")
    img_b64_str = request_dict.pop("image")  # image is an encoded base64 string
    max_new_tokens = request_dict.pop("max_new_tokens", 100)
    # image = PIL.Image.open(requests.get(image_path, stream=True, timeout=3000).raw)
    image = PIL.Image.open(BytesIO(base64.b64decode(img_b64_str)))

    generate_kwargs = {
        "lazy_mode": True,
        "hpu_graphs": use_hpu_graphs,
        "max_new_tokens": max_new_tokens,
        "ignore_eos": False,
    }

    start = time.time()
    result = generator(image, prompt=prompt, batch_size=1, generate_kwargs=generate_kwargs)
    end = time.time()
    result = result[0]["generated_text"].split("ASSISTANT: ")[-1]
    print(f"result = {result}, time = {(end-start) * 1000 }ms")
    ret = {"text": result}
    return JSONResponse(ret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model_name_or_path", type=str, default="llava-hf/llava-1.5-7b-hf")
    parser.add_argument("--use_hpu_graphs", default=True, action="store_true")
    parser.add_argument("--warmup", type=int, default=3, help="Number of warmup iterations for benchmarking.")
    parser.add_argument("--bf16", default=True, action="store_true")

    args = parser.parse_args()
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
        device="hpu",
    )

    # warmup
    generate_kwargs = {
        "lazy_mode": True,
        "hpu_graphs": args.use_hpu_graphs,
        "max_new_tokens": 100,
        "ignore_eos": False,
    }
    if args.use_hpu_graphs:
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
