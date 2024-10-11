# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import os
import threading
import time
from io import BytesIO
from typing import Union

import requests
import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor

from comps import (
    CustomLogger,
    LVMDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("lvm-llama-vision-native")
logflag = os.getenv("LOGFLAG", False)
initialization_lock = threading.Lock()
initialized = False


def initialize():
    global model, processor, initialized
    with initialization_lock:
        if not initialized:

            model_id = os.getenv("LLAMA_VISION_MODEL_ID", "meta-llama/Llama-3.2-11B-Vision-Instruct")
            huggingface_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
            model = AutoModelForVision2Seq.from_pretrained(
                model_id, device_map="hpu", torch_dtype=torch.bfloat16, token=huggingface_token
            )
            processor = AutoProcessor.from_pretrained(model_id, token=huggingface_token)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": "If I had to write a haiku for this one, it would be: "},
                    ],
                }
            ]
            url = "https://llava-vl.github.io/static/images/view.jpg"
            raw_image = Image.open(requests.get(url, stream=True).raw)
            prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
            inputs = processor(raw_image, prompt, return_tensors="pt").to(model.device)
            prompt_len = len(inputs["input_ids"][0])
            output = model.generate(**inputs, pad_token_id=0, max_new_tokens=32)
            generated_tokens = output[:, prompt_len:]
            logger.info(processor.decode(generated_tokens[0], skip_special_tokens=True))
            initialized = True
            logger.info("[LVM] Llama Vision LVM initialized.")


@register_microservice(
    name="opea_service@lvm_llama_vision_native",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9399,
)
@register_statistics(names=["opea_service@lvm_llama_vision_native"])
async def lvm(request: Union[LVMDoc]) -> Union[TextDoc]:
    initialize()
    if logflag:
        logger.info(request)
    start = time.time()
    img_b64_str = request.image
    prompt = request.prompt
    max_new_tokens = request.max_new_tokens

    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    text = processor.apply_chat_template(messages, add_generation_prompt=True)
    image_data = base64.b64decode(img_b64_str)
    image_stream = BytesIO(image_data)
    raw_image = Image.open(image_stream)

    inputs = processor(raw_image, text, return_tensors="pt").to(model.device)
    prompt_len = len(inputs["input_ids"][0])
    output = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
    generated_tokens = output[:, prompt_len:]
    result = processor.decode(generated_tokens[0], skip_special_tokens=True)
    statistics_dict["opea_service@lvm_llama_vision_native"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(result)

    return TextDoc(text=result)


if __name__ == "__main__":
    opea_microservices["opea_service@lvm_llama_vision_native"].start()
