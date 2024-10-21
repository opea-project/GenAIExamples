# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2013--2023, librosa development team.
# Copyright 1999-2003 The OpenLDAP Foundation, Redwood City, California, USA.  All Rights Reserved.
# Copyright (c) 2012, Anaconda, Inc. All rights reserved.

import json
import os
import time

import requests

# GenAIComps
from comps import CustomLogger

logger = CustomLogger("animation")
logflag = os.getenv("LOGFLAG", False)
from comps import (
    Base64ByteStrDoc,
    ServiceType,
    VideoPath,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


# Register the microservice
@register_microservice(
    name="opea_service@animation",
    service_type=ServiceType.ANIMATION,
    endpoint="/v1/animation",
    host="0.0.0.0",
    port=9066,
    input_datatype=Base64ByteStrDoc,
    output_datatype=VideoPath,
)
@register_statistics(names=["opea_service@animation"])
async def animate(audio: Base64ByteStrDoc):
    start = time.time()

    byte_str = audio.byte_str
    inputs = {"audio": byte_str}
    if logflag:
        logger.info(inputs)

    response = requests.post(url=f"{wav2lip_endpoint}/v1/wav2lip", data=json.dumps(inputs), proxies={"http": None})

    outfile = response.json()["wav2lip_result"]
    if logflag:
        logger.info(response)
        logger.info(f"Video generated successfully, check {outfile} for the result.")

    statistics_dict["opea_service@animation"].append_latency(time.time() - start, None)
    return VideoPath(video_path=outfile)


if __name__ == "__main__":
    wav2lip_endpoint = os.getenv("WAV2LIP_ENDPOINT", "http://localhost:7860")
    logger.info("[animation - router] Animation initialized.")
    opea_microservices["opea_service@animation"].start()
