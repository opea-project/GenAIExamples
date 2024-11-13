# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import json
import os

import requests

# Get the root folder of the current script
root_folder = os.path.dirname(os.path.abspath(__file__))


def video_to_audio(path_to_video):
    """Convert a video file to an audio file in base64 format by sending a request to the server.

    Args:
        path_to_video (str): Path to the video file.

    Returns:
        str: Base64 encoded audio file.
    """
    file_name = os.path.join(root_folder, path_to_video)

    # Read the video file and encode it in base64
    with open(file_name, "rb") as f:
        video_base64_str = base64.b64encode(f.read()).decode("utf-8")

    # Define the endpoint and payload
    endpoint = "http://localhost:7078/v1/video2audio"
    inputs = {"byte_str": video_base64_str}

    # Send the POST request to the server
    response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})

    # Check if the request was successful
    response.raise_for_status()

    # Extract the base64 encoded audio from the response
    audio_base64 = response.json()["byte_str"]

    return audio_base64


def read_config():
    """Function to read the configuration parameters from the input file.
    Returns the parsed arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Process configuration parameters.")

    # Add argument for the video file path
    parser.add_argument(
        "--path_to_video",
        help="Location of the video file that will be converted to audio.",
        required=False,
        default=os.path.join(root_folder, "../data/intel_short.mp4"),
    )

    # Add argument for the audio file path
    parser.add_argument(
        "--path_to_audio",
        help="Location to save the extracted audio file.",
        required=False,
        default=os.path.join(root_folder, "converted_audio.wav"),
    )

    # Parse the arguments
    args = parser.parse_args()

    # Return the parsed arguments
    return args


if __name__ == "__main__":
    # Read the configuration parameters
    args = read_config()

    # Extract audio from video
    audio_base64 = video_to_audio(args.path_to_video)

    # Save the extracted audio to a file
    with open(args.path_to_audio, "wb") as f:
        f.write(base64.b64decode(audio_base64))

    print("========= Audio file saved as ======")
    print(args.path_to_audio)
    print("====================================")
