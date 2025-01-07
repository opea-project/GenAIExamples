# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from fastapi.responses import StreamingResponse
from integrations.opea_gptsovits import OpeaGptsovitsTts
from integrations.opea_speecht5 import OpeaSpeecht5Tts

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import AudioSpeechRequest

logger = CustomLogger("opea_tts_microservice")
logflag = os.getenv("LOGFLAG", False)

tts_component_name = os.getenv("TTS_COMPONENT_NAME", "OPEA_SPEECHT5_TTS")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(tts_component_name, description=f"OPEA TTS Component: {tts_component_name}")


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
        # Use the loader to invoke the component
        tts_response = await loader.invoke(request)
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
