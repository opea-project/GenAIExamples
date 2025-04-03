# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Literal

from utils import AUDIO_FORMATS, IMAGE_FORMATS, convert_audio_to_base64, get_b64_frame_from_timestamp


class SeparatorStyle(Enum):
    """Different separator style."""

    SINGLE = auto()


@dataclasses.dataclass
class Conversation:
    """A class that keeps all conversation history."""

    system: str
    roles: List[str]
    chatbot_history: List[Dict[str, Any]]
    offset: int
    sep_style: SeparatorStyle = SeparatorStyle.SINGLE
    sep: str = "\n"
    video_file: str = None
    caption: str = None
    time_of_frame_ms: str = None
    base64_frame: str = None
    skip_next: bool = False
    split_audio: str = None
    split_video: str = None
    image: str = None
    audio_query_file: str = None
    pdf: str = None

    def _template_caption(self):
        out = ""
        if self.caption is not None:
            out = f"The caption associated with the image is '{self.caption}'. "
        return out

    def get_prompt(self, is_very_first_query):
        conv_dict = [{"role": "user", "content": []}]
        caption_flag = True
        is_image_query = False

        for record in self.chatbot_history:
            role = record["role"]
            content = record["content"]

            if role == "user":
                # Check if last entry of conv_dict has role user
                if conv_dict[-1]["role"] != "user":
                    conv_dict.append({"role": "user", "content": []})
            elif role == "assistant":
                caption_flag = False
                # Check if last entry of conv_dict has role assistant
                if conv_dict[-1]["role"] != "assistant":
                    conv_dict.append({"role": "assistant", "content": []})

            # Add content to the last conv_dict record. The single space has only effect on first image-only
            # query for the similarity search results to get expected response.
            if isinstance(content, str):
                if caption_flag:
                    content += " " + self._template_caption()
                conv_dict[-1]["content"].append({"type": "text", "text": content})

            if isinstance(content, dict) and "path" in content:
                if Path(content["path"]).suffix in IMAGE_FORMATS:
                    is_image_query = True
                    conv_dict[-1]["content"].append(
                        {"type": "image_url", "image_url": {"url": get_b64_frame_from_timestamp(content["path"], 0)}}
                    )
                if Path(content["path"]).suffix in AUDIO_FORMATS:
                    conv_dict[-1]["content"].append(
                        {"type": "audio", "audio": convert_audio_to_base64(content["path"])}
                    )

            # include the image from the assistant's response given the user's is not a image query
            if not is_image_query and caption_flag and self.image:
                conv_dict[-1]["content"].append(
                    {"type": "image_url", "image_url": {"url": get_b64_frame_from_timestamp(self.image, 0)}}
                )

        return conv_dict

    def get_b64_image(self):
        b64_img = None
        if self.time_of_frame_ms and self.video_file:
            time_of_frame_ms = self.time_of_frame_ms
            video_file = self.video_file
            b64_img = get_b64_frame_from_timestamp(video_file, time_of_frame_ms)
        return b64_img

    def get_b64_audio_query(self):
        b64_audio = None
        if self.audio_query_file:
            b64_audio = convert_audio_to_base64(self.audio_query_file)
        return b64_audio

    def to_gradio_chatbot(self):
        return self.chatbot_history

    def copy(self):
        return Conversation(
            system=self.system,
            roles=self.roles,
            chatbot_history=self.chatbot_history,
            offset=self.offset,
            sep_style=self.sep_style,
            sep=self.sep,
            video_file=self.video_file,
            caption=self.caption,
            base64_frame=self.base64_frame,
        )

    def dict(self):
        return {
            "system": self.system,
            "roles": self.roles,
            "chatbot_history": self.chatbot_history,
            "offset": self.offset,
            "sep": self.sep,
            "time_of_frame_ms": self.time_of_frame_ms,
            "video_file": self.video_file,
            "caption": self.caption,
            "base64_frame": self.base64_frame,
            "split_audio": self.split_audio,
            "split_video": self.split_video,
            "image": self.image,
            "audio_query_file": self.audio_query_file,
            "pdf": self.pdf,
        }


multimodalqna_conv = Conversation(
    system="",
    roles=("user", "assistant"),
    chatbot_history=[],
    offset=0,
    sep_style=SeparatorStyle.SINGLE,
    sep="\n",
    video_file=None,
    caption=None,
    time_of_frame_ms=None,
    base64_frame=None,
    split_audio=None,
    split_video=None,
    image=None,
    audio_query_file=None,
    pdf=None,
)
