# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import os
import time

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    SDImg2ImgInputs,
    SDOutputs,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.image2image.src.integrations.native import OpeaImageToImage

args = None

logger = CustomLogger("image2image")

component_loader = None


@register_microservice(
    name="opea_service@image2image",
    service_type=ServiceType.IMAGE2IMAGE,
    endpoint="/v1/image2image",
    host="0.0.0.0",
    port=9389,
    input_datatype=SDImg2ImgInputs,
    output_datatype=SDOutputs,
)
@register_statistics(names=["opea_service@image2image"])
async def image2image(input: SDImg2ImgInputs):
    start = time.time()
    results = await component_loader.invoke(input)
    statistics_dict["opea_service@image2image"].append_latency(time.time() - start, None)
    return SDOutputs(images=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="stabilityai/stable-diffusion-xl-refiner-1.0")
    parser.add_argument("--use_hpu_graphs", default=False, action="store_true")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bf16", action="store_true")

    args = parser.parse_args()
    image2image_component_name = os.getenv("IMAGE2IMAGE_COMPONENT_NAME", "OPEA_IMAGE2IMAGE")
    # Register components
    try:
        # Initialize OpeaComponentLoader
        component_loader = OpeaComponentLoader(
            image2image_component_name,
            description=f"OPEA IMAGE2IMAGE Component: {image2image_component_name}",
            config=args.__dict__,
        )
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        exit(1)

    logger.info("Image2image server started.")
    opea_microservices["opea_service@image2image"].start()
