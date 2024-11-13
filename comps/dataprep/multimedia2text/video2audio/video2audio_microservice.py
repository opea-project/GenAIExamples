# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
import uuid

import requests

from comps import (
    Base64ByteStrDoc,
    CustomLogger,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
)
from comps.dataprep.multimedia2text.video2audio.video2audio import Video2Audio

# Initialize custom logger
logger = CustomLogger("video2audio")
logflag = os.getenv("LOGFLAG", False)


# Register the microservice
@register_microservice(
    name="opea_service@video2audio",
    service_type=ServiceType.DATAPREP,
    endpoint="/v1/video2audio",
    host="0.0.0.0",
    port=7078,
    input_datatype=Base64ByteStrDoc,
    output_datatype=Base64ByteStrDoc,
)
@register_statistics(names=["opea_service@video2audio"])
async def audio_to_text(request: Base64ByteStrDoc):
    """Convert video to audio and return the result in base64 format.

    Args:
        request (Base64ByteStrDoc): The incoming request containing the video in base64 format.

    Returns:
        Base64ByteStrDoc: The response containing the audio in base64 format.
    """
    try:
        # Generate a unique identifier for the video file
        uid = str(uuid.uuid4())
        file_name = uid + ".mp4"

        logger.info("Received request for video to audio conversion.")
        byte_str = request.byte_str

        # Decode the base64 string and save it as a video file
        with open(file_name, "wb") as f:
            f.write(base64.b64decode(byte_str))

        # Convert the video file to audio and get the result in base64 format
        response = v2a.convert_video_to_audio_base64(file_name)

        # Remove the temporary video file
        os.remove(file_name)

        logger.info("Successfully converted video to audio.")
        return Base64ByteStrDoc(byte_str=response)

    except requests.RequestException as e:
        logger.error(f"Request to video-to-audio endpoint failed: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during video to audio conversion: {e}")
        raise


if __name__ == "__main__":
    try:
        # Initialize the Video2Audio instance
        v2a = Video2Audio()

        # Log initialization message
        logger.info("[video2audio - router] VIDEO2AUDIO initialized.")

        # Start the microservice
        opea_microservices["opea_service@video2audio"].start()

    except Exception as e:
        logger.error(f"Failed to start the microservice: {e}")
        raise
