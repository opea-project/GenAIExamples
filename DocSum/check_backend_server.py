# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
import argparse
import requests

# Get the root folder of the current script
root_folder = os.path.dirname(os.path.abspath(__file__))
endpoint = "http://localhost:8888/v1/docsum"

def get_base64_str(file_name):
    with open(file_name, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def summarize():
    
    # file_name = '/localdisk/mcetin/GenAIComps/comps/dataprep/docsum/data/test_video_10s.wav'
    
    # file_name = 'comps/dataprep/docsum/data/test_video_60s.wav'
    # file_name = 'comps/dataprep/docsum/data/test_full.wav'
    # test_audio_base64_str = get_base64_str(file_name)
    # inputs = {"type": "audio", "messages": test_audio_base64_str} 
    
    # # file_name = 'comps/dataprep/docsum/data/test_video_60s.wav'
    file_name = 'comps/dataprep/docsum/data/test_full.mp4'
    test_audio_base64_str = get_base64_str(file_name)
    inputs = {"type": "video", "messages": test_audio_base64_str} 
    
    inputs = {"type": "text", "messages": " THIS IS A TEST >>>> and a number of states are starting to adopt them voluntarily special correspondent john delenco of education week reports it takes just 10 minutes to cross through gillette wyoming this small city sits in the northeast corner of the state surrounded by 100s of miles of prairie but schools here in campbell county are on the edge of something big the next generation science standards you are going to build a strand of dna and you are going to decode it and figure out what that dna actually says for christy mathis at sage valley junior high school the new standards are about learning to think like a scientist there is a lot of really good stuff in them every standard is a performance task it is not you know the child needs to memorize these things it is the student needs to be able to do some pretty intense stuff we are analyzing we are critiquing we are ."} 

    response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})

    # print(response.json())
    
        
    # text_cont = "and a number of states are starting to adopt them voluntarily special correspondent john delenco of education week reports it takes just 10 minutes to cross through gillette wyoming this small city sits in the northeast corner of the state surrounded by 100s of miles of prairie but schools here in campbell county are on the edge of something big the next generation science standards you are going to build a strand of dna and you are going to decode it and figure out what that dna actually says for christy mathis at sage valley junior high school the new standards are about learning to think like a scientist there is a lot of really good stuff in them every standard is a performance task it is not you know the child needs to memorize these things it is the student needs to be able to do some pretty intense stuff we are analyzing we are critiquing we are ."
    
    # # Define the endpoint and payload
    # inputs = {"messages": text_cont}
    
    # # Send the POST request to the server
    # response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
    
    # # Check if the request was successful
    # response.raise_for_status()
    
    
    import ast 
    temp = ast.literal_eval( 
        [i.split('data: ')[1] for i in response.text.split('\n\n') if "/logs/LLMChain/final_output" in i][0] 
    )['ops']
    
    response = [i['value'] for i in temp if i['path'] == "/logs/LLMChain/final_output"][0]
    
    print(response)

def read_config():
    """
    Function to read the configuration parameters from the input file.
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
        default=os.path.join(root_folder, "../../GenAIComps/comps/dataprep/docsum/data/test.mp4")
    )
    
    # Add argument for the audio file path
    parser.add_argument(
        "--path_to_audio",
        help="Location to save the extracted audio file.",
        required=False,
        default=os.path.join(root_folder, "converted_audio.mp3"),
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Return the parsed arguments
    return args

if __name__ == "__main__":
    # Read the configuration parameters
    args = read_config()
    
    summarize()

    # Extract audio from video
    # audio_base64 = video_to_audio(args.path_to_video)
    
    
    
    
    # # Save the extracted audio to a file
    # with open(args.path_to_audio, "wb") as f:
    #     f.write(base64.b64decode(audio_base64))
        
    # print("========= Audio file saved as ======")
    # print(args.path_to_audio)
    # print("====================================")
    
   