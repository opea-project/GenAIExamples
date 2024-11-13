# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import json
import os

import requests

# Get the root folder of the current script
root_folder = os.path.dirname(os.path.abspath(__file__))


def audio_to_text(path_to_audio):
    """Convert an audio file to text by sending a request to the server.

    Args:
        path_to_audio (str): Path to the audio file.

    Returns:
        str: The transcribed text.
    """
    file_name = os.path.join(root_folder, path_to_audio)

    # Read the audio file and encode it in base64
    with open(file_name, "rb") as f:
        audio_base64_str = base64.b64encode(f.read()).decode("utf-8")

    endpoint = "http://localhost:9099/v1/audio/transcriptions"
    inputs = {"byte_str": audio_base64_str}

    # Send the POST request to the server
    response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})

    # Check if the request was successful
    response.raise_for_status()

    # Return the transcribed text
    return response.json()["query"]


def check_response(response):
    """Check the response from the server and print the result.

    Args:
        response (str): The transcribed text from the server.
    """
    expected_response = "well"
    assert response == expected_response, f"Expected '{expected_response}', but got '{response}'"
    print("Test passed successfully!")


def read_config():
    """Read the configuration parameters from the input file.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Process configuration parameters.")

    # Add argument for the audio file path
    parser.add_argument(
        "--path_to_audio",
        help="Location of the audio file that will be converted to text.",
        required=False,
        default=os.path.join(root_folder, "../data/intel_short.wav"),
    )

    # Parse the arguments
    args = parser.parse_args()

    # Return the parsed arguments
    return args


if __name__ == "__main__":
    # Read the configuration parameters
    args = read_config()

    # Convert audio to text
    response = audio_to_text(args.path_to_audio)

    # Check the response
    check_response(response)
