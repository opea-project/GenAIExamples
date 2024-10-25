import base64
import json
import os
import requests
import ast

# Get the root folder of the current script
root_folder = os.path.dirname(os.path.abspath(__file__))

def get_base64_str(file_name):
    """
    Convert a file to a base64 encoded string.

    Args:
        file_name (str): Path to the file.

    Returns:
        str: Base64 encoded string of the file content.
    """
    with open(file_name, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def post_request(endpoint, inputs, headers=None):
    """
    Send a POST request to the specified endpoint.

    Args:
        endpoint (str): The URL of the endpoint.
        inputs (dict): The data to be sent in the request.
        headers (dict, optional): The headers to be sent in the request.

    Returns:
        requests.Response: The response from the server.
    """
    return requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None}, headers=headers)

def read_response(response):
    """
    Parse the response from the server.

    Args:
        response (requests.Response): The response from the server.

    Returns:
        str: The parsed response content.
    """
    
    return response.text.replace("'\n\ndata: b'", "").replace("data: b' ", "").replace("</s>'\n\ndata: [DONE]\n\n","").replace("\n\ndata: b", "").replace("'\n\n", "").replace("'\n", "").replace('''\'"''' ,"")

def input_data_for_test(document_type):
    """
    Generate input data for testing based on the document type.

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
        input_data = get_base64_str(os.path.join(root_folder, 'data/test_audio_30s.wav'))
    elif document_type == "video":
        # input_data = get_base64_str(os.path.join(root_folder, 'data/test_video_30s.mp4'))
        input_data = get_base64_str(os.path.join(root_folder, 'data/test_full.mp4'))
    else:
        raise ValueError("Invalid document type")
    
    return input_data

def validate_response(response, service_name):
    """
    Validate the response from the server.

    Args:
        response (requests.Response): The response from the server.
        service_name (str): The name of the service being tested.

    Raises:
        AssertionError: If the response status code is not 200.
    """
    assert response.status_code == 200, f"{service_name} service failed to get response from the server. Status code: {response.status_code}"
    print(f">>> {service_name} service Test Passed ... ")
    print()

def test_whisper_service():
    """
    Test the Whisper service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Whisper service")
    document_type = 'audio'
    endpoint = "http://localhost:7066/v1/asr"
    inputs = {"audio": input_data_for_test(document_type)}
    
    response = post_request(endpoint, inputs)
    
    validate_response(response, "Whisper")

def test_audio2text():
    """
    Test the Audio2Text service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Audio2Text service")
    document_type = 'audio'
    endpoint = "http://localhost:9099/v1/audio/transcriptions"
    inputs = {"byte_str": input_data_for_test(document_type)}
    
    response = post_request(endpoint, inputs)
    
    validate_response(response, "Audio2Text")

def test_video2text():
    """
    Test the Video2Text service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: Video2Text service")
    document_type = 'video'
    endpoint = "http://localhost:7078/v1/video2audio"
    inputs = {"byte_str": input_data_for_test(document_type)}
    
    response = post_request(endpoint, inputs)
    
    validate_response(response, "Video2Text")

def test_docsum_data():
    """
    Test the Docsum Data service for different document types.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print(f"Running test: Docsum Data service")
    for document_type in ['text', 'audio', 'video']:
        endpoint = "http://localhost:7079/v1/docsum/dataprep"
        inputs = {document_type: input_data_for_test(document_type)}
        
        response = post_request(endpoint, inputs)
        
        validate_response(response, f"Docsum Data ({document_type})")

def test_tgi_service():
    """
    Test the TGI service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: tgi-service service")
    
    endpoint = "http://localhost:8008/generate"
    
    # Define the JSON payload
    inputs = {
        "inputs": "What is Deep Learning?",
        "parameters": {
            "max_new_tokens": 17,
            "do_sample": True
        }
    }

    # Define the headers
    headers = {
        "Content-Type": "application/json"
    }
        
    # Send the POST request
    response = post_request(endpoint, inputs, headers=headers)
    
    validate_response(response, "tgi-service")

def test_llm_service():
    """
    Test the LLM service.

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print("Running test: llm-service service")
    
    endpoint = "http://localhost:9000/v1/chat/docsum"
    
    # Define the JSON payload
    inputs = {
        "query": input_data_for_test('text'),
        "parameters": {
            "max_new_tokens": 17,
            "do_sample": True
        }
    }

    # Define the headers
    headers = {
        "Content-Type": "application/json"
    }
        
    # Send the POST request
    response = post_request(endpoint, inputs, headers=headers)
    
    validate_response(response, "llm-service")

def test_e2e_megaservice(document_type='video'):
    """
    Test the end-to-end Megaservice.

    Args:
        document_type (str): The type of document ("text", "audio", or "video").

    Raises:
        AssertionError: If the service does not return a 200 status code.
    """
    print(f"Running test: E2E Megaservice for {document_type}")
    endpoint = "http://localhost:8888/v1/docsum"
    inputs = {"type": document_type, "messages": input_data_for_test(document_type)}
    
    response = post_request(endpoint, inputs)
    
    validate_response(response, "E2E Megaservice")
    
    print(read_response(response))

if __name__ == "__main__":
    # Run the tests and print the results
    try:
        test_tgi_service()
        test_llm_service()        
        test_whisper_service()
        test_audio2text()
        test_video2text()
        test_docsum_data()
        test_e2e_megaservice()
    except AssertionError as e:
        print(f"Test failed: {e}")
        
        