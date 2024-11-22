# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import base64
import uuid
from os import path, remove

from moviepy import VideoFileClip

# Get the root folder of the current script
root_folder = path.dirname(path.abspath(__file__))


class Video2Audio:
    """Class to convert video files to audio files and handle base64 encoding."""

    def __init__(self):
        pass

    def validate_file_exists(self, file_path):
        """Validate if the given file exists.

        Args:
            file_path (str): Path to the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

    def convert_video_to_audio(self, path_to_video, audio_file_name):
        """Extract mp3 audio file from mp4 video file.

        Args:
            path_to_video (str): Path to the video file.
            audio_file_name (str): Path to save the extracted audio file.
        """
        # Validate the video file exists
        self.validate_file_exists(path_to_video)

        # Extract audio from video
        clip = VideoFileClip(path_to_video)
        clip.audio.write_audiofile(audio_file_name)
        print(f"Audio extracted and saved to {audio_file_name}")

    def convert_base64(self, file_name):
        """Convert a file to a base64 encoded string and remove the file.

        Args:
            file_name (str): Path to the file to be encoded.

        Returns:
            str: Base64 encoded string of the file content.
        """
        # Validate the file exists
        self.validate_file_exists(file_name)

        # Read the file and encode it in base64
        with open(file_name, "rb") as f:
            base64_str = base64.b64encode(f.read()).decode("utf-8")

        # Remove the file after encoding
        remove(file_name)

        return base64_str

    def convert_video_to_audio_base64(self, video_file_name):
        """Convert a video file to an audio file and return the audio file as a base64 encoded string.

        Args:
            video_file_name (str): Path to the video file.

        Returns:
            str: Base64 encoded string of the extracted audio file.
        """
        # Generate a unique identifier for the audio file
        uid = str(uuid.uuid4())
        audio_file_name = uid + ".mp3"

        # Convert the video to audio
        self.convert_video_to_audio(video_file_name, audio_file_name)

        # Convert the audio file to a base64 encoded string
        base64_str = self.convert_base64(audio_file_name)

        return base64_str
