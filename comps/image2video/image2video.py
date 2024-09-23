# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os
import time

import requests

from comps import (
    ImagesPath,
    ServiceType,
    VideoPath,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


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
    images_path = [img.image_path for img in input.images_path]
    inputs = {"images_path": images_path}
    video_path = requests.post(url=f"{svd_endpoint}/generate", data=json.dumps(inputs), proxies={"http": None}).json()[
        "video_path"
    ]

    statistics_dict["opea_service@image2video"].append_latency(time.time() - start, None)
    return VideoPath(video_path=video_path)


if __name__ == "__main__":
    svd_endpoint = os.getenv("SVD_ENDPOINT", "http://localhost:9368")
    print("Image2video server started.")
    opea_microservices["opea_service@image2video"].start()
