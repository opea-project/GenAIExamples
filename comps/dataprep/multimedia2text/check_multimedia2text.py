# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
import base64
import json
import os

import requests

# Get the root folder of the current script
root_folder = os.path.dirname(os.path.abspath(__file__))


def get_base64_str(file_name):
    """Convert a file to a base64 encoded string.

    Args:
        file_name (str): Path to the file.

    Returns:
        str: Base64 encoded string of the file content.
    """
    with open(file_name, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def post_request(endpoint, inputs):
    """Send a POST request to the specified endpoint.

    Args:
        endpoint (str): The URL of the endpoint.
        inputs (dict): The data to be sent in the request.

    Returns:
        requests.Response: The response from the server.
    """
    return requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})


def input_data_for_test(document_type):
    """Generate input data for testing based on the document type.

    Args:
        document_type (str): The type of document ("text", "audio", or "video").

    Returns:
        str: The input data for testing.

    Raises:
        ValueError: If the document type is invalid.
    """
    if document_type == "text":
        input_data = "THIS IS A TEST >>>> and a number of states are starting to adopt them voluntarily special correspondent john delenco of education week reports it takes just 10 minutes to cross through gillette wyoming this small city sits in the northeast corner of the state surrounded by 100s of miles of prairie but schools here in campbell county are on the edge of something big the next generation science standards you are going to build a strand of dna and you are going to decode it and figure out what that dna actually says for christy mathis at sage valley junior high school the new standards are about learning to think like a scientist there is a lot of really good stuff in them every standard is a performance task it is not you know the child needs to memorize these things it is the student needs to be able to do some pretty intense stuff we are analyzing we are critiquing we are."
    elif document_type == "audio":
        input_data = get_base64_str(os.path.join(root_folder, "data/intel_short.wav"))
    elif document_type == "video":
        input_data = get_base64_str(os.path.join(root_folder, "data/intel_short.mp4"))
    else:
        raise ValueError("Invalid document type")

    return input_data


def test_whisper_service():
    """Test the Whisper service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Whisper service")
    document_type = "audio"
    endpoint = "http://localhost:7066/v1/asr"
    inputs = {"audio": input_data_for_test(document_type)}
    response = post_request(endpoint, inputs)
    assert (
        response.status_code == 200
    ), f"Whisper service failed to get response from the server. Status code: {response.status_code}"

    # If the response status code is 200, print "Test passed"
    print(">>> Whisper service Test Passed ... ")
    print()


def test_audio2text():
    """Test the Audio2Text service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Audio2Text service")
    document_type = "audio"
    endpoint = "http://localhost:9099/v1/audio/transcriptions"
    inputs = {"byte_str": input_data_for_test(document_type)}
    response = post_request(endpoint, inputs)
    assert (
        response.status_code == 200
    ), f"Audio2Text service failed to get response from the server. Status code: {response.status_code}"

    # If the response status code is 200, print "Test passed"
    print(">>> Audio2Text service Test Passed ... ")
    print()


def test_video2text():
    """Test the Video2Text service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Video2Text service")
    document_type = "video"
    endpoint = "http://localhost:7078/v1/video2audio"
    inputs = {"byte_str": input_data_for_test(document_type)}
    response = post_request(endpoint, inputs)
    assert (
        response.status_code == 200
    ), f"Video2Text service failed to get response from the server. Status code: {response.status_code}"

    # If the response status code is 200, print "Test passed"
    print(">>> Video2Text service Test Passed ... ")
    print()


def test_multimedia2text_data():
    """Test the multimedia2text service for different document types.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Multimedia2text service")
    for document_type in ["text", "audio", "video"]:
        endpoint = "http://localhost:7079/v1/multimedia2text"
        inputs = {document_type: input_data_for_test(document_type)}
        response = post_request(endpoint, inputs)
        assert (
            response.status_code == 200
        ), f"{document_type} service failed to get response from the server. Status code: {response.status_code}"

        # If the response status code is 200, print "Test passed"
        print(f">>> Multimedia2text service test for {document_type} data type passed ... ")
    print()


if __name__ == "__main__":
    # Run the tests and print the results
    try:
        test_whisper_service()
        test_audio2text()
        test_video2text()
        test_multimedia2text_data()

    except AssertionError as e:
        print(f"Test failed: {e}")
