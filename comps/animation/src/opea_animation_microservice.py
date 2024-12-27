# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2013--2023, librosa development team.
# Copyright 1999-2003 The OpenLDAP Foundation, Redwood City, California, USA.  All Rights Reserved.
# Copyright (c) 2012, Anaconda, Inc. All rights reserved.

import json
import os
import time

# GenAIComps
from comps import CustomLogger, OpeaComponentController
from comps.animation.src.integration.opea import OpeaAnimation

logger = CustomLogger("opea_animation")
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

# Initialize OpeaComponentController
controller = OpeaComponentController()

# Register components
try:
    # Instantiate Animation component and register it to controller
    opea_animation = OpeaAnimation(
        name="OpeaAnimation",
        description="OPEA Animation Service",
    )
    controller.register(opea_animation)

    # Discover and activate a healthy component
    controller.discover_and_activate()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")


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
def animate(audio: Base64ByteStrDoc):
    start = time.time()

    outfile = opea_animation.invoke(audio.byte_str)
    if logflag:
        logger.info(f"Video generated successfully, check {outfile} for the result.")

    statistics_dict["opea_service@animation"].append_latency(time.time() - start, None)
    return VideoPath(video_path=outfile)


if __name__ == "__main__":
    logger.info("[animation - router] Animation initialized.")
    opea_microservices["opea_service@animation"].start()
