# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import time

from comps import (
    CustomLogger,
    ImagesPath,
    OpeaComponentLoader,
    ServiceType,
    VideoPath,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.image2video.src.integrations.native import OpeaImage2video

logger = CustomLogger("opea_image2video_microservice")

component_loader = None


@register_microservice(
    name="opea_service@image2video",
    service_type=ServiceType.IMAGE2VIDEO,
    endpoint="/v1/image2video",
    host="0.0.0.0",
    port=9369,
    input_datatype=ImagesPath,
    output_datatype=VideoPath,
)
@register_statistics(names=["opea_service@image2video"])
async def image2video(input: ImagesPath):
    start = time.time()
    try:
        # Use the loader to invoke the component
        results = await component_loader.invoke(input)
        statistics_dict["opea_service@image2video"].append_latency(time.time() - start, None)
        return results
    except Exception as e:
        logger.error(f"Error during image2video invocation: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9368)
    parser.add_argument("--model_name_or_path", type=str, default="stabilityai/stable-video-diffusion-img2vid-xt")
    parser.add_argument("--use_hpu_graphs", default=False, action="store_true")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    image2video_component_name = os.getenv("IMAGE2VIDEO_COMPONENT_NAME", "OPEA_IMAGE2VIDEO")
    # Register components
    try:
        # Initialize OpeaComponentLoader
        component_loader = OpeaComponentLoader(
            image2video_component_name,
            description=f"OPEA IMAGE2VIDEO Component: {image2video_component_name}",
            config=args.__dict__,
        )
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        exit(1)

    logger.info("Image2video server started.")
    opea_microservices["opea_service@image2video"].start()
