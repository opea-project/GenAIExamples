# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
import uuid
from pathlib import Path
from typing import Iterator

import cv2
import requests
import webvtt
import whisper
from moviepy.editor import VideoFileClip


def create_upload_folder(upload_path):
    """Create a directory to store uploaded video data."""
    if not os.path.exists(upload_path):
        Path(upload_path).mkdir(parents=True, exist_ok=True)


def load_json_file(file_path):
    """Read contents of json file."""
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def clear_upload_folder(upload_path):
    """Clear the upload directory."""
    for root, dirs, files in os.walk(upload_path, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.rmdir(dir_path)


def generate_video_id():
    """Generates a unique identifier for a video file."""
    return str(uuid.uuid4())


def convert_video_to_audio(video_path: str, output_audio_path: str):
    """Converts video to audio using MoviePy library that uses `ffmpeg` under the hood.

    :param video_path: file path of video file (.mp4)
    :param output_audio_path: file path of audio file (.wav) to be created
    """
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_audio_path)
    video_clip.close()
    audio_clip.close()


def load_whisper_model(model_name: str = "base"):
    """Load a whisper model for generating video transcripts."""
    return whisper.load_model(model_name)


def extract_transcript_from_audio(whisper_model, audio_path: str):
    """Generate transcript from audio file.

    :param whisper_model: a pre-loaded whisper model object
    :param audio_path: file path of audio file (.wav)
    """
    options = dict(task="translate", best_of=5, language="en")
    return whisper_model.transcribe(audio_path, **options)


def format_timestamp_for_transcript(seconds: float, always_include_hours: bool = True, fractionalSeperator: str = "."):
    """Format timestamp for video transcripts."""
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d}{fractionalSeperator}{milliseconds:03d}"


def write_vtt(transcript: Iterator[dict], vtt_path: str):
    """Write transcripts to a .vtt file."""
    with open(vtt_path, "a") as file:
        file.write("WEBVTT\n\n")
        for segment in transcript["segments"]:
            text = (segment["text"]).replace("-->", "->")
            file.write(
                f"{format_timestamp_for_transcript(segment['start'])} --> {format_timestamp_for_transcript(segment['end'])}\n"
            )
            file.write(f"{text.strip()}\n\n")


def delete_audio_file(audio_path: str):
    """Delete audio file after extracting transcript."""
    os.remove(audio_path)


def time_to_frame(time: float, fps: float):
    """Convert time in seconds into frame number."""
    return int(time * fps - 1)


def str2time(strtime: str):
    """Get time in seconds from string."""
    strtime = strtime.strip('"')
    hrs, mins, seconds = [float(c) for c in strtime.split(":")]

    total_seconds = hrs * 60**2 + mins * 60 + seconds

    return total_seconds


def convert_img_to_base64(image):
    "Convert image to base64 string"
    _, buffer = cv2.imencode(".jpg", image)
    encoded_string = base64.b64encode(buffer)
    return encoded_string.decode()


def extract_frames_and_annotations_from_transcripts(video_id: str, video_path: str, vtt_path: str, output_dir: str):
    """Extract frames (.jpg) and annotations (.json) from video file (.mp4) and captions file (.vtt)"""
    # Set up location to store frames and annotations
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "frames"), exist_ok=True)

    # Load video and get fps
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)

    # read captions file
    captions = webvtt.read(vtt_path)

    annotations = []
    for idx, caption in enumerate(captions):
        start_time = str2time(caption.start)
        end_time = str2time(caption.end)

        mid_time = (end_time + start_time) / 2
        text = caption.text.replace("\n", " ")

        frame_no = time_to_frame(mid_time, fps)
        mid_time_ms = mid_time * 1000
        vidcap.set(cv2.CAP_PROP_POS_MSEC, mid_time_ms)
        success, frame = vidcap.read()

        if success:
            # Save frame for further processing
            img_fname = f"frame_{idx}"
            img_fpath = os.path.join(output_dir, "frames", img_fname + ".jpg")
            cv2.imwrite(img_fpath, frame)

            # Convert image to base64 encoded string
            b64_img_str = convert_img_to_base64(frame)

            # Create annotations for frame from transcripts
            annotations.append(
                {
                    "video_id": video_id,
                    "video_name": os.path.basename(video_path),
                    "b64_img_str": b64_img_str,
                    "caption": text,
                    "time": mid_time_ms,
                    "frame_no": frame_no,
                    "sub_video_id": idx,
                }
            )

    # Save transcript annotations as json file for further processing
    with open(os.path.join(output_dir, "annotations.json"), "w") as f:
        json.dump(annotations, f)

    vidcap.release()
    return annotations


def use_lvm(endpoint: str, img_b64_string: str, prompt: str = "Provide a short description for this scene."):
    """Generate image captions/descriptions using LVM microservice."""
    inputs = {"image": img_b64_string, "prompt": prompt, "max_new_tokens": 32}
    response = requests.post(url=endpoint, data=json.dumps(inputs))
    print(response)
    return response.json()["text"]


def extract_frames_and_generate_captions(
    video_id: str, video_path: str, lvm_endpoint: str, output_dir: str, key_frame_per_second: int = 1
):
    """Extract frames (.jpg) and annotations (.json) from video file (.mp4) by generating captions using LVM microservice."""
    # Set up location to store frames and annotations
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "frames"), exist_ok=True)

    # Load video and get fps
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)

    annotations = []
    hop = round(fps / key_frame_per_second)
    curr_frame = 0
    idx = -1

    while True:
        ret, frame = vidcap.read()
        if not ret:
            break

        if curr_frame % hop == 0:
            idx += 1

            mid_time = vidcap.get(cv2.CAP_PROP_POS_MSEC)
            mid_time_ms = mid_time * 1000

            frame_no = curr_frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Save frame for further processing
            img_fname = f"frame_{idx}"
            img_fpath = os.path.join(output_dir, "frames", img_fname + ".jpg")
            cv2.imwrite(img_fpath, frame)

            # Convert image to base64 encoded string
            b64_img_str = convert_img_to_base64(frame)

            # Caption generation using LVM microservice
            caption = use_lvm(lvm_endpoint, b64_img_str)
            caption = caption.strip()
            text = caption.replace("\n", " ")

            # Create annotations for frame from transcripts
            annotations.append(
                {
                    "video_id": video_id,
                    "video_name": os.path.basename(video_path),
                    "b64_img_str": b64_img_str,
                    "caption": text,
                    "time": mid_time_ms,
                    "frame_no": frame_no,
                    "sub_video_id": idx,
                }
            )

        curr_frame += 1

    # Save caption annotations as json file for further processing
    with open(os.path.join(output_dir, "annotations.json"), "w") as f:
        json.dump(annotations, f)

    vidcap.release()
