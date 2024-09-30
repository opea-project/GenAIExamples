# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Union

import deepspeed
import deepspeed.comm as dist
import requests
import torch
import uvicorn
from fastapi import FastAPI
from huggingface_hub import snapshot_download
from PIL import Image
from starlette.middleware.cors import CORSMiddleware
from transformers import AutoProcessor, MllamaForConditionalGeneration
from transformers.utils import is_offline_mode

from comps import CustomLogger, LVMDoc, TextDoc

app = FastAPI(title="NeuralChat Gaudi Serving Process", description="Serving", version="0.0.1")
logger = CustomLogger("lvm-llama-vision-tp")
logflag = os.getenv("LOGFLAG", False)
model = None
model_id = os.getenv("MODEL_ID", "/workspace/models/final_weights/Llama-3.2-90B-Vision-Instruct")
processor = None
initialization_lock = threading.Lock()
initialized = False
local_rank = 0

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins as necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def print_rank0(*msg):
    if local_rank != 0:
        return
    print(*msg)


def get_repo_root(model_name_or_path):
    huggingface_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if os.path.exists(model_name_or_path):
        # local path
        return model_name_or_path
    # checks if online or not
    if is_offline_mode():
        print_rank0("Offline mode: forcing local_files_only=True")
    # download only on first process
    allow_patterns = ["*.bin", "*.model", "*.json", "*.txt", "*.py", "*LICENSE"]
    if local_rank == 0:
        snapshot_download(
            model_name_or_path,
            local_files_only=is_offline_mode(),
            cache_dir=os.getenv("TRANSFORMERS_CACHE", None),
            allow_patterns=allow_patterns,
            token=huggingface_token,
            # ignore_patterns=["*.safetensors"],
        )

    dist.barrier()

    return snapshot_download(
        model_name_or_path,
        local_files_only=is_offline_mode(),
        cache_dir=os.getenv("TRANSFORMERS_CACHE", None),
        allow_patterns=allow_patterns,
        token=huggingface_token,
        # ignore_patterns=["*.safetensors"],
    )


def get_checkpoint_files(model_name_or_path):
    cached_repo_dir = get_repo_root(model_name_or_path)

    # extensions: .bin | .pt
    # creates a list of paths from all downloaded files in cache dir
    file_list = [
        str(entry)
        for entry in Path(cached_repo_dir).rglob("*.[sbp][ait][fn][e][t][e][n][s][o][r][s]")
        if entry.is_file()
    ]
    print(file_list)
    return file_list


def write_checkpoints_json(local_rank, checkpoints_json):
    checkpoint_files = get_checkpoint_files(model_id)
    if local_rank == 0:
        # model.config.model_type.upper()
        data = {"type": "BLOOM", "checkpoints": checkpoint_files, "version": 1.0}
        json.dump(data, open(checkpoints_json, "w"))


def get_int_from_env(env_keys, default):
    """Returns the first positive env value found in the `env_keys` list or the default."""
    for e in env_keys:
        val = int(os.environ.get(e, -1))
        if val >= 0:
            return val
    return default


def generate(prompt, raw_image, max_new_tokens=32):
    if logflag:
        logger.info(f"[lvm tp serve] start to generate text with {prompt}")
    inputs = processor(raw_image, prompt, return_tensors="pt").to(torch.device("hpu"))
    prompt_len = len(inputs["input_ids"][0])
    output = model.generate(**inputs, max_new_tokens=max_new_tokens)
    generated_tokens = output[:, prompt_len:]
    result = processor.decode(generated_tokens[0], skip_special_tokens=True)
    if logflag:
        logger.info(f"[lvm tp serve] text generated: {result}")
    return result


def initialize():
    global model, processor, initialized, local_rank
    if logflag:
        logger.info("[lvm tp serve] start to initialize model and processor")
    initialized = True
    huggingface_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    model = MllamaForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.bfloat16, device_map="auto", token=huggingface_token
    )
    processor = AutoProcessor.from_pretrained(model_id, token=huggingface_token)

    deepspeed.init_distributed(dist_backend="hccl")
    local_rank = get_int_from_env(["LOCAL_RANK", "MPI_LOCALRANKID"], "0")
    world_size = get_int_from_env(["WORLD_SIZE", "PMI_SIZE"], "1")
    if logflag:
        logger.info(f"[lvm tp serve] local rank: {local_rank}, world size: {world_size}")

    repo_root = get_repo_root(model_id)
    checkpoints_json = "checkpoints.json"
    write_checkpoints_json(local_rank, checkpoints_json)
    if logflag:
        logger.info("[lvm tp serve] checkpoint json written")

    # sleep for 10 seconds to avoid multi-process conflict
    time.sleep(10)
    model = deepspeed.init_inference(
        model,
        mp_size=world_size,
        base_dir=repo_root,
        dtype=torch.bfloat16,
        checkpoint=checkpoints_json,
    )
    if logflag:
        logger.info(model)
        logger.info("[lvm tp serve] model initialized")

    # warm up model
    if logflag:
        logger.info("[lvm tp serve] start to warm up model")
    warmup = 3
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "If I had to write a haiku for this one, it would be: "},
            ],
        }
    ]
    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    url = "https://llava-vl.github.io/static/images/view.jpg"
    raw_image = Image.open(requests.get(url, stream=True).raw)
    for i in range(warmup):
        if logflag:
            logger.info(f"[lvm tp serve] warming up iteration {i}")
        generate(input_text, raw_image)


@app.post("/v1/lvm_serve")
async def lvm_tp_endpoint(input: Union[LVMDoc]) -> Union[TextDoc]:
    if logflag:
        logger.info(input)

    img_b64_str = input.image
    prompt = input.prompt
    max_new_tokens = input.max_new_tokens
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    text = processor.apply_chat_template(messages, add_generation_prompt=True)
    image_data = base64.b64decode(img_b64_str)
    image_stream = BytesIO(image_data)
    raw_image = Image.open(image_stream)

    result = generate(text, raw_image, max_new_tokens)
    if logflag:
        logger.info(f"res: {result}")
    return TextDoc(text=result)


if __name__ == "__main__":
    initialize()
    process_port = 9393 + local_rank + 1
    try:
        uvicorn.run(app, host="localhost", port=process_port)
    except Exception as e:
        print(f"Error starting uvicorn: {str(e)}")
