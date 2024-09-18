# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from enum import Enum, auto
from typing import List

from utils import get_b64_frame_from_timestamp


class SeparatorStyle(Enum):
    """Different separator style."""

    SINGLE = auto()


@dataclasses.dataclass
class Conversation:
    """A class that keeps all conversation history."""

    system: str
    roles: List[str]
    messages: List[List[str]]
    offset: int
    sep_style: SeparatorStyle = SeparatorStyle.SINGLE
    sep: str = "\n"
    video_file: str = None
    caption: str = None
    time_of_frame_ms: str = None
    base64_frame: str = None
    skip_next: bool = False
    split_video: str = None

    def _template_caption(self):
        out = ""
        if self.caption is not None:
            out = f"The caption associated with the image is '{self.caption}'. "
        return out

    def get_prompt(self):
        messages = self.messages
        if len(messages) > 1 and messages[1][1] is None:
            # Need to do RAG. prompt is the query only
            ret = messages[0][1]
        else:
            # No need to do RAG. Thus, prompt of chatcompletion format
            conv_dict = []
            if self.sep_style == SeparatorStyle.SINGLE:
                for i, (role, message) in enumerate(messages):
                    if message:
                        if i != 0:
                            dic = {"role": role, "content": message}
                        else:
                            dic = {"role": role}
                            if self.time_of_frame_ms and self.video_file:
                                content = [{"type": "text", "text": message}]
                                if self.base64_frame:
                                    base64_frame = self.base64_frame
                                else:
                                    base64_frame = get_b64_frame_from_timestamp(self.video_file, self.time_of_frame_ms)
                                    self.base64_frame = base64_frame
                                content.append({"type": "image_url", "image_url": {"url": base64_frame}})
                            else:
                                content = message
                            dic["content"] = content
                        conv_dict.append(dic)
            else:
                raise ValueError(f"Invalid style: {self.sep_style}")
            ret = conv_dict
        return ret

    def append_message(self, role, message):
        self.messages.append([role, message])

    def get_b64_image(self):
        b64_img = None
        if self.time_of_frame_ms and self.video_file:
            time_of_frame_ms = self.time_of_frame_ms
            video_file = self.video_file
            b64_img = get_b64_frame_from_timestamp(video_file, time_of_frame_ms)
        return b64_img

    def to_gradio_chatbot(self):
        ret = []
        for i, (role, msg) in enumerate(self.messages[self.offset :]):
            if i % 2 == 0:
                if type(msg) is tuple:
                    import base64
                    from io import BytesIO

                    msg, image, image_process_mode = msg
                    max_hw, min_hw = max(image.size), min(image.size)
                    aspect_ratio = max_hw / min_hw
                    max_len, min_len = 800, 400
                    shortest_edge = int(min(max_len / aspect_ratio, min_len, min_hw))
                    longest_edge = int(shortest_edge * aspect_ratio)
                    W, H = image.size
                    if H > W:
                        H, W = longest_edge, shortest_edge
                    else:
                        H, W = shortest_edge, longest_edge
                    image = image.resize((W, H))
                    buffered = BytesIO()
                    image.save(buffered, format="JPEG")
                    img_b64_str = base64.b64encode(buffered.getvalue()).decode()
                    img_str = f'<img src="data:image/png;base64,{img_b64_str}" alt="user upload image" />'
                    msg = img_str + msg.replace("<image>", "").strip()
                    ret.append([msg, None])
                else:
                    ret.append([msg, None])
            else:
                ret[-1][-1] = msg
        return ret

    def copy(self):
        return Conversation(
            system=self.system,
            roles=self.roles,
            messages=[[x, y] for x, y in self.messages],
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
            "messages": self.messages,
            "offset": self.offset,
            "sep": self.sep,
            "time_of_frame_ms": self.time_of_frame_ms,
            "video_file": self.video_file,
            "caption": self.caption,
            "base64_frame": self.base64_frame,
            "split_video": self.split_video,
        }


multimodalqna_conv = Conversation(
    system="",
    roles=("user", "assistant"),
    messages=(),
    offset=0,
    sep_style=SeparatorStyle.SINGLE,
    sep="\n",
    video_file=None,
    caption=None,
    time_of_frame_ms=None,
    base64_frame=None,
    split_video=None,
)
