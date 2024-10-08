# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import os
import threading
import time

import torch
from diffusers import DiffusionPipeline

from comps import (
    CustomLogger,
    SDInputs,
    SDOutputs,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("text2image")
pipe = None
args = None
initialization_lock = threading.Lock()
initialized = False


def initialize():
    global pipe, args, initialized
    with initialization_lock:
        if not initialized:
            # initialize model and tokenizer
            if os.getenv("MODEL", None):
                args.model_name_or_path = os.getenv("MODEL")
            kwargs = {}
            if args.bf16:
                kwargs["torch_dtype"] = torch.bfloat16
            if not args.token:
                args.token = os.getenv("HF_TOKEN")
            if args.device == "hpu":
                kwargs.update(
                    {
                        "use_habana": True,
                        "use_hpu_graphs": args.use_hpu_graphs,
                        "gaudi_config": "Habana/stable-diffusion",
                        "token": args.token,
                    }
                )
                if "stable-diffusion-3" in args.model_name_or_path:
                    from optimum.habana.diffusers import GaudiStableDiffusion3Pipeline

                    pipe = GaudiStableDiffusion3Pipeline.from_pretrained(
                        args.model_name_or_path,
                        **kwargs,
                    )
                elif "stable-diffusion" in args.model_name_or_path.lower() or "flux" in args.model_name_or_path.lower():
                    from optimum.habana.diffusers import AutoPipelineForText2Image

                    pipe = AutoPipelineForText2Image.from_pretrained(
                        args.model_name_or_path,
                        **kwargs,
                    )
                else:
                    raise NotImplementedError(
                        "Only support stable-diffusion, stable-diffusion-xl, stable-diffusion-3 and flux now, "
                        + f"model {args.model_name_or_path} not supported."
                    )
            elif args.device == "cpu":
                pipe = DiffusionPipeline.from_pretrained(args.model_name_or_path, token=args.token, **kwargs)
            else:
                raise NotImplementedError(f"Only support cpu and hpu device now, device {args.device} not supported.")
            logger.info("Stable Diffusion model initialized.")
            initialized = True


@register_microservice(
    name="opea_service@text2image",
    service_type=ServiceType.TEXT2IMAGE,
    endpoint="/v1/text2image",
    host="0.0.0.0",
    port=9379,
    input_datatype=SDInputs,
    output_datatype=SDOutputs,
)
@register_statistics(names=["opea_service@text2image"])
def text2image(input: SDInputs):
    initialize()
    start = time.time()
    prompt = input.prompt
    num_images_per_prompt = input.num_images_per_prompt

    generator = torch.manual_seed(args.seed)
    images = pipe(prompt, generator=generator, num_images_per_prompt=num_images_per_prompt).images
    image_path = os.path.join(os.getcwd(), prompt.strip().replace(" ", "_").replace("/", ""))
    os.makedirs(image_path, exist_ok=True)
    results = []
    for i, image in enumerate(images):
        save_path = os.path.join(image_path, f"image_{i+1}.png")
        image.save(save_path)
        with open(save_path, "rb") as f:
            bytes = f.read()
        b64_str = base64.b64encode(bytes).decode()
        results.append(b64_str)
    statistics_dict["opea_service@text2image"].append_latency(time.time() - start, None)
    return SDOutputs(images=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="stabilityai/stable-diffusion-3-medium-diffusers")
    parser.add_argument("--use_hpu_graphs", default=False, action="store_true")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bf16", action="store_true")

    args = parser.parse_args()

    logger.info("Text2image server started.")
    opea_microservices["opea_service@text2image"].start()
