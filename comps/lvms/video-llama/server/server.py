# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Stand-alone video llama FastAPI Server."""

import argparse
import logging
import os
import re
from threading import Thread
from urllib.parse import urlparse

import decord
import requests
import uvicorn
import validators
from extract_vl_embedding import VLEmbeddingExtractor as VL
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field
from transformers import TextIteratorStreamer, set_seed
from video_llama.common.registry import registry
from video_llama.conversation.conversation_video import Chat
from werkzeug.utils import secure_filename

# Initialize decord bridge and seed
decord.bridge.set_bridge("torch")
set_seed(22)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Define global variables
context_db = None
streamer = None
chat = None

VIDEO_DIR = "/home/user/comps/lvms/video-llama/server/data"

CFG_PATH = "video_llama_config/video_llama_eval_only_vl.yaml"
MODEL_TYPE = "llama_v2"

os.makedirs(VIDEO_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request validation
class videoInfo(BaseModel):
    video_path: str = Field(..., description="URL of the video to be processed, support remote")
    start_time: float = Field(..., descrciption="video clip start time in seconds", example=0.0)
    duration: float = Field(..., description="video clip duration in seconds", example=10.0)


class GenerateRequest(BaseModel):
    start_time: float = Field(..., descrciption="video clip start time in seconds", example=0.0)
    duration: float = Field(..., description="video clip duration in seconds", example=10.0)
    prompt: str = Field(..., description="Query for Video-LLama", example="What is the man doing?")
    max_new_tokens: int = Field(default=512, description="Maximum number of tokens to generate", example=512)  #


# Function to construct instructions context
def construct_instructions():
    instructions = [
        """ Identify the person [with specific features / seen at a specific location / performing a specific action] in the provided data based on the video content.
        Describe in detail the relevant actions of the individuals mentioned in the question.
        Provide full details of their actions being performed and roles. Focus on the individual and the actions being performed.
        Exclude information about their age and items on the shelf that are not directly observable.
        Do not mention items on the shelf that are not  visible. \
        Exclude information about the background and surrounding details.
        Ensure all information is distinct, accurate, and directly observable.
        Do not repeat actions of individuals and do not mention anything about other persons not visible in the video.
        Mention actions and roles once only.
        """,
        """Analyze the provided data to recognize and describe the activities performed by individuals.
        Specify the type of activity and any relevant contextual details,
        Do not give repetitions, always give distinct and accurate information only.""",
        """Determine the interactions between individuals and items in the provided data.
        Describe the nature of the interaction between individuals and the items involved.
        Provide full details of their relevant actions and roles. Focus on the individuals and the action being performed by them.
        Exclude information about their age and items on the shelf that are not directly observable.
        Exclude information about the background and surrounding details.
        Ensure all information is distinct, accurate, and directly observable.
        Do not repeat actions of individuals and do not mention anything about other persons not visible in the video.
        Do not mention  items on the shelf that are not observable. \
        """,
        """Analyze the provided data to answer queries based on specific time intervals.
        Provide detailed information corresponding to the specified time frames,
        Do not give repetitions, always give distinct and accurate information only.""",
        """Identify individuals based on their appearance as described in the provided data.
        Provide details about their identity and actions,
        Do not give repetitions, always give distinct and accurate information only.""",
        """Answer questions related to events and activities that occurred on a specific day.
        Provide a detailed account of the events,
        Do not give repetitions, always give distinct and accurate information only.""",
    ]
    HFembeddings = HuggingFaceEmbeddings(model_kwargs={"device": "cpu"})
    context = FAISS.from_texts(instructions, HFembeddings)
    return context


# Helper functions for chat and inference
def get_context(query, context):
    context = context.similarity_search(query)
    return [i.page_content for i in context]


def chat_reset(chat_state, img_list):
    logging.info("-" * 30)
    logging.info("resetting chatState")
    if chat_state is not None:
        chat_state.messages = []
    if img_list is not None:
        img_list = []
    return chat_state, img_list


def inference(chat: Chat, streamer, video: videoInfo, instruction: str, max_new_tokens: int):
    logging.info("Video-Llama generation begin.")
    video_path = video.video_path
    start_time = video.start_time
    duration = video.duration

    chat.upload_video_without_audio(video_path, start_time, duration)
    chat.ask("<rag_prompt>" + instruction)
    chat.answer(
        max_new_tokens=max_new_tokens,
        num_beams=1,
        min_length=1,
        top_p=0.9,
        repetition_penalty=1.0,
        length_penalty=1,
        temperature=0.02,
        max_length=2000,
        keep_conv_hist=True,
        streamer=streamer,
    )
    if "similar video" not in instruction:
        logging.info("Resetting the chat history")
        chat.clear()
    logging.info("Video-Llama generation done, remove video.")
    os.remove(video_path)


def stream_res(video, instruction, max_new_tokens):
    logging.debug("Start to stream...")
    thread = Thread(target=inference, args=(chat, streamer, video, instruction, max_new_tokens))
    thread.start()
    for text in streamer:
        yield text


def is_local_file(url):
    """Returns True if url is a local file, False otherwise."""
    return not url.startswith("http://") and not url.startswith("https://")


def is_valid_url(url):
    # Validate the URL's structure
    validation = validators.url(url)
    if not validation:
        logging.error("URL is invalid")
        return False

    # Parse the URL to components
    parsed_url = urlparse(url)

    # Check the scheme
    if parsed_url.scheme not in ["http", "https"]:
        logging.error("URL scheme is invalid")
        return False

    # Check for "../" in the path
    if "../" in parsed_url.path:
        logging.error("URL contains '../', which is not allowed")
        return False

    # Check that the path only contains one "." for the file extension
    if parsed_url.path.count(".") != 1:
        logging.error("URL path does not meet the requirement of having only one '.'")
        return False

    # If all checks pass, the URL is valid
    logging.info("URL is valid")
    return True


def is_valid_video(filename):
    if re.match(r"^[a-zA-Z0-9-_]+\.(mp4)$", filename, re.IGNORECASE):
        return secure_filename(filename)
    else:
        return False


@app.get("/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/generate", response_class=StreamingResponse)
async def generate(
    video_url: str = Query(..., description="remote URL of the video to be processed"),
    start: float = Query(..., description="video clip start time in seconds", examples=0.0),
    duration: float = Query(..., description="video clip duration in seconds", examples=10.0),
    prompt: str = Query(..., description="Query for Video-LLama", examples="What is the man doing?"),
    max_new_tokens: int = Query(150, description="Maximum number of tokens to generate", examples=150),
) -> StreamingResponse:

    if video_url.lower().endswith(".mp4"):
        logging.info(f"Format check passed, the file '{video_url}' is an MP4 file.")
    else:
        logging.info(f"Format check failed, the file '{video_url}' is not an MP4 file.")
        return JSONResponse(status_code=500, content={"message": "Invalid file type. Only mp4 videos are allowed."})

    if is_local_file(video_url):
        # validate the video name
        if is_valid_video(video_url):
            secure_video_name = is_valid_video(video_url)  # only support video name without path
        else:
            return JSONResponse(status_code=500, content={"message": "Invalid file name."})

        video_path = os.path.join(VIDEO_DIR, secure_video_name)
        if os.path.exists(video_path):
            logging.info(f"File found: {video_path}")
        else:
            logging.error(f"File not found: {video_path}")
            return JSONResponse(
                status_code=404, content={"message": "File not found. Only local files under data folder are allowed."}
            )
    else:
        # validate the remote URL
        if not is_valid_url(video_url):
            return JSONResponse(status_code=500, content={"message": "Invalid URL."})
        else:
            parsed_url = urlparse(video_url)
            video_path = os.path.join(VIDEO_DIR, os.path.basename(parsed_url.path))
            try:
                response = requests.get(video_url, stream=True)
                if response.status_code == 200:
                    with open(video_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:  # filter out keep-alive new chunks
                                file.write(chunk)
                    logging.info(f"File downloaded: {video_path}")
                else:
                    logging.info(f"Error downloading file: {response.status_code}")
                    return JSONResponse(status_code=500, content={"message": "Error downloading file."})
            except Exception as e:
                logging.info(f"Error downloading file: {response.status_code}")
                return JSONResponse(status_code=500, content={"message": "Error downloading file."})

    video_info = videoInfo(start_time=start, duration=duration, video_path=video_path)

    # format context and instruction
    instruction = f"{get_context(prompt,context_db)[0]}: {prompt}"

    # logging.info("instruction:",instruction)

    return StreamingResponse(stream_res(video_info, instruction, max_new_tokens))


# Main entry point
parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="0.0.0.0")
parser.add_argument("--port", type=int, default=9009)
args = parser.parse_args()

context_db = construct_instructions()
video_llama = VL(cfg_path=CFG_PATH, model_type=MODEL_TYPE)
tokenizer = video_llama.model.llama_tokenizer
streamer = TextIteratorStreamer(tokenizer, skip_prompt=True)

vis_processor_cfg = video_llama.cfg.datasets_cfg.webvid.vis_processor.train
vis_processor = registry.get_processor_class(vis_processor_cfg.name).from_config(vis_processor_cfg)

chat = Chat(video_llama.model, vis_processor, device="cpu")

uvicorn.run(app, host=args.host, port=args.port)
