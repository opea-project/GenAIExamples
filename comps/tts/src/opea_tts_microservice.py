# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from fastapi.responses import StreamingResponse
from integrations.opea_gptsovits import OpeaGptsovitsTts
from integrations.opea_speecht5 import OpeaSpeecht5Tts

from comps import (
    CustomLogger,
    OpeaComponentController,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import AudioSpeechRequest

logger = CustomLogger("opea_tts_microservice")
logflag = os.getenv("LOGFLAG", False)

# Initialize OpeaComponentController
controller = OpeaComponentController()

# Register components
try:
    # Instantiate TTS components
    opea_speecht5 = OpeaSpeecht5Tts(
        name="OpeaSpeecht5Tts",
        description="OPEA SpeechT5 TTS Service",
    )

    opea_gptsovits = OpeaGptsovitsTts(
        name="OpeaGptsovitsTts",
        description="OPEA GPTSoVITS TTS Service",
    )

    # Register components with the controller
    controller.register(opea_speecht5)
    controller.register(opea_gptsovits)

    # Discover and activate a healthy component
    controller.discover_and_activate()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")


async def stream_forwarder(response):
    """Forward the stream chunks to the client using iter_content."""
    for chunk in response.iter_content(chunk_size=1024):
        yield chunk


@register_microservice(
    name="opea_service@tts",
    service_type=ServiceType.TTS,
    endpoint="/v1/audio/speech",
    host="0.0.0.0",
    port=9088,
    input_datatype=AudioSpeechRequest,
    output_datatype=StreamingResponse,
)
@register_statistics(names=["opea_service@tts"])
async def text_to_speech(request: AudioSpeechRequest) -> StreamingResponse:
    start = time.time()

    if logflag:
        logger.info(f"Input received: {request}")

    try:
        # Use the controller to invoke the active component
        tts_response = controller.invoke(request)
        if logflag:
            logger.info(tts_response)
        statistics_dict["opea_service@tts"].append_latency(time.time() - start, None)
        return StreamingResponse(stream_forwarder(tts_response))

    except Exception as e:
        logger.error(f"Error during tts invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA TTS Microservice is starting....")
    opea_microservices["opea_service@tts"].start()
