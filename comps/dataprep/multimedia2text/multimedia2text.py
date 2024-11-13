# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

import requests

from comps import CustomLogger

# Initialize custom logger
logger = CustomLogger("multimedia2text")

from comps import Audio2text, DocSumDoc, ServiceType, opea_microservices, register_microservice, register_statistics


# Register the microservice
@register_microservice(
    name="opea_service@multimedia2text",
    service_type=ServiceType.ASR,
    endpoint="/v1/multimedia2text",
    host="0.0.0.0",
    port=7079,
    input_datatype=DocSumDoc,
    output_datatype=Audio2text,
)
@register_statistics(names=["opea_service@multimedia2text"])
async def audio_to_text(input: DocSumDoc):
    """Convert video or audio input to text using external services.

    Args:
        input (DocSumDoc): Input document containing video, audio, or text data.

    Returns:
        Audio2text: Object containing the ASR result or input text.
    """
    response_to_return = None

    # Process video input
    if input.video is not None:
        logger.info(f"Processing video input at {v2a_endpoint}/v1/video2audio")
        inputs = {"byte_str": input.video}
        response = requests.post(url=f"{v2a_endpoint}/v1/video2audio", data=json.dumps(inputs), proxies={"http": None})
        response.raise_for_status()  # Ensure the request was successful
        input.audio = response.json().get("byte_str")
        if input.audio is None:
            logger.error("Failed to extract audio from video")
            raise ValueError("Failed to extract audio from video")

    # Process audio input
    if input.audio is not None:
        logger.info(f"Processing audio input at {a2t_endpoint}/v1/asr")
        inputs = {"audio": input.audio}
        response = requests.post(url=f"{a2t_endpoint}/v1/asr", data=json.dumps(inputs), proxies={"http": None})
        response.raise_for_status()  # Ensure the request was successful
        response_to_return = response.json().get("asr_result")
        if response_to_return is None:
            logger.error("Failed to get ASR result from audio")
            raise ValueError("Failed to get ASR result from audio")

    # Process text input
    if input.text is not None:
        logger.info("Processing text input")
        response_to_return = input.text

    if response_to_return is None:
        logger.warning("No valid input provided")
        response_to_return = "No input"
    else:
        logger.info("Data Processing completeed")

    return Audio2text(query=response_to_return)


if __name__ == "__main__":
    try:
        # Get the V2T endpoint from environment variables or use the default
        v2a_endpoint = os.getenv("V2A_ENDPOINT", "http://localhost:7078")
        # Get the A2T endpoint from environment variables or use the default
        a2t_endpoint = os.getenv("A2T_ENDPOINT", "http://localhost:7066")

        # Log initialization message
        logger.info("[multimedia2text - router] multimedia2text initialized.")

        # Start the microservice
        opea_microservices["opea_service@multimedia2text"].start()

    except Exception as e:
        logger.error(f"Failed to start the multimedia2text microservice: {e}")
        raise
