# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import time

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    SDInputs,
    SDOutputs,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.text2image.src.integrations.native import OpeaText2image

logger = CustomLogger("opea_text2image_microservice")


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
async def text2image(input: SDInputs):
    start = time.time()
    try:
        # Use the loader to invoke the active component
        results = await loader.invoke(input)
        statistics_dict["opea_service@text2image"].append_latency(time.time() - start, None)
        return results
    except Exception as e:
        logger.error(f"Error during text2image invocation: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="stabilityai/stable-diffusion-3-medium-diffusers")
    parser.add_argument("--use_hpu_graphs", default=False, action="store_true")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bf16", action="store_true")

    args = parser.parse_args()

    text2image_component_name = os.getenv("TEXT2IMAGE_COMPONENT_NAME", "OPEA_TEXT2IMAGE")
    # Initialize OpeaComponentLoader
    loader = OpeaComponentLoader(
        text2image_component_name,
        description=f"OPEA TEXT2IMAGE Component: {text2image_component_name}",
        config=args.__dict__,
    )

    logger.info("Text2image server started.")
    opea_microservices["opea_service@text2image"].start()
