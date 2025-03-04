# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from pathlib import Path
from enum import Enum, auto
from typing import Dict, List, Any, Literal

from utils import convert_audio_to_base64, get_b64_frame_from_timestamp, GRADIO_IMAGE_FORMATS, GRADIO_AUDIO_FORMATS


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
        conv_dict = []
        
        if is_very_first_query:
            conv_dict.append({'role': 'user', 'content': []})
            for item in self.chatbot_history:
                content = item['content']
                
                if isinstance(content, str):
                    conv_dict[-1]['content'].append({'type': 'text', 'text': content})
                elif isinstance(content, dict) and 'path' in content:
                    if Path(content['path']).suffix in GRADIO_IMAGE_FORMATS:
                        conv_dict[-1]['content'].append({'type': 'image_url', 'image_url': {'url': get_b64_frame_from_timestamp(content['path'], 0)}})
                    if Path(content['path']).suffix in GRADIO_AUDIO_FORMATS:
                        conv_dict[-1]['content'].append({'type': 'audio', 'audio': convert_audio_to_base64(content['path'])})
        else:
            # print(f'chatbot history: \n{self.chatbot_history}')
            for i, item in enumerate(self.chatbot_history):
                role = item['role']
                content = item['content']
                
                if i == 0:
                    conv_dict.append({'role': role, 'content': []})
                    
                
                if role == 'user':
                    if conv_dict[-1]['role'] != 'user':
                        conv_dict.append({'role': role, 'content': []})
                    
                    if isinstance(content, str):
                        conv_dict[-1]['content'].append({'type': 'text', 'text': content})
                    elif isinstance(content, dict) and 'path' in content:
                        if Path(content['path']).suffix in GRADIO_IMAGE_FORMATS:
                            conv_dict[-1]['content'].append({'type': 'image_url', 'image_url': {'url': get_b64_frame_from_timestamp(content['path'], 0)}})
                        if Path(content['path']).suffix in GRADIO_AUDIO_FORMATS:
                            conv_dict[-1]['content'].append({'type': 'audio', 'audio': convert_audio_to_base64(content['path'])})
                elif role == 'assistant':
                    if conv_dict[-1]['role'] != 'assistant':
                        conv_dict.append({'role': role, 'content': []})
                    if isinstance(content, str):
                        conv_dict[-1]['content'] = content
                                        
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
    split_video=None,
    image=None,
    audio_query_file=None,
    pdf=None,
)
