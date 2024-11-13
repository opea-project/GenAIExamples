# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

import requests

from comps import CustomLogger

# Initialize custom logger
logger = CustomLogger("a2t")
logflag = os.getenv("LOGFLAG", False)

from comps import (
    Audio2text,
    Base64ByteStrDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
)


# Register the microservice
@register_microservice(
    name="opea_service@a2t",
    service_type=ServiceType.ASR,
    endpoint="/v1/audio/transcriptions",
    host="0.0.0.0",
    port=9099,
    input_datatype=Base64ByteStrDoc,
    output_datatype=Audio2text,
)
@register_statistics(names=["opea_service@a2t"])
async def audio_to_text(audio: Base64ByteStrDoc):
    """Convert audio to text and return the transcription.

    Args:
        audio (Base64ByteStrDoc): The incoming request containing the audio in base64 format.

    Returns:
        TextDoc: The response containing the transcription text.
    """
    try:
        # Validate the input
        if not audio or not audio.byte_str:
            raise ValueError("Invalid input: 'audio' or 'audio.byte_str' is missing.")

        byte_str = audio.byte_str
        inputs = {"audio": byte_str}

        if logflag:
            logger.info(f"Inputs: {inputs}")

        # Send the POST request to the ASR endpoint
        response = requests.post(url=f"{a2t_endpoint}/v1/asr", data=json.dumps(inputs), proxies={"http": None})
        response.raise_for_status()  # Raise an error for bad status codes

        if logflag:
            logger.info(f"Response: {response.json()}")

        # Return the transcription result
        return Audio2text(query=response.json()["asr_result"])  # .text

    except requests.RequestException as e:
        logger.error(f"Request to ASR endpoint failed: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during audio to text conversion: {e}")
        raise


if __name__ == "__main__":
    try:
        # Get the ASR endpoint from environment variables or use the default
        a2t_endpoint = os.getenv("A2T_ENDPOINT", "http://localhost:7066")

        # Log initialization message
        logger.info("[a2t - router] A2T initialized.")

        # Start the microservice
        opea_microservices["opea_service@a2t"].start()

    except Exception as e:
        logger.error(f"Failed to start the microservice: {e}")
        raise
