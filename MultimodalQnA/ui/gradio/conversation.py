# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from enum import Enum, auto
from typing import Dict, List

from PIL import Image
from utils import convert_audio_to_base64, get_b64_frame_from_timestamp


class SeparatorStyle(Enum):
    """Different separator style."""

    SINGLE = auto()


@dataclasses.dataclass
class Conversation:
    """A class that keeps all conversation history."""

    system: str
    roles: List[str]
    messages: List[List[str]]
    image_query_files: Dict[int, str]
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

    def get_prompt(self):
        messages = self.messages
        if len(messages) > 1 and messages[1][1] is None:
            # Need to do RAG. If the query is text, prompt is the query only
            if self.audio_query_file:
                ret = [{"role": "user", "content": [{"type": "audio", "audio": self.get_b64_audio_query()}]}]
            elif 0 in self.image_query_files:
                b64_image = get_b64_frame_from_timestamp(self.image_query_files[0], 0)
                ret = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": messages[0][1]},
                            {"type": "image_url", "image_url": {"url": b64_image}},
                        ],
                    }
                ]
            else:
                ret = messages[0][1]
        else:
            # No need to do RAG. Thus, prompt of chatcompletion format
            conv_dict = []
            if self.sep_style == SeparatorStyle.SINGLE:
                for i, (role, message) in enumerate(messages):
                    if message:
                        dic = {"role": role}
                        content = [{"type": "text", "text": message}]
                        # There might be audio
                        if self.audio_query_file:
                            content.append({"type": "audio", "audio": self.get_b64_audio_query()})
                        # There might be a returned item from the first query
                        if i == 0 and self.time_of_frame_ms and self.video_file:
                            base64_frame = (
                                self.base64_frame
                                if self.base64_frame
                                else get_b64_frame_from_timestamp(self.video_file, self.time_of_frame_ms)
                            )
                            if base64_frame is None:
                                base64_frame = ""
                            # Include the original caption for the returned image/video
                            if self.caption and content[0]["type"] == "text":
                                content[0]["text"] = content[0]["text"] + " " + self._template_caption()
                            content.append({"type": "image_url", "image_url": {"url": base64_frame}})
                        # There might be a query image
                        if i in self.image_query_files:
                            content.append(
                                {
                                    "type": "image_url",
                                    "image_url": {"url": get_b64_frame_from_timestamp(self.image_query_files[i], 0)},
                                }
                            )
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

    def get_b64_audio_query(self):
        b64_audio = None
        if self.audio_query_file:
            b64_audio = convert_audio_to_base64(self.audio_query_file)
        return b64_audio

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
                elif i in self.image_query_files:
                    import base64
                    from io import BytesIO

                    image = Image.open(self.image_query_files[i])
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
                    if image.format not in ["JPEG", "JPG"]:
                        image = image.convert("RGB")
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
            image_query_files=self.image_query_files,
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
            "image": self.image,
            "audio_query_file": self.audio_query_file,
            "pdf": self.pdf,
        }


multimodalqna_conv = Conversation(
    system="",
    roles=("user", "assistant"),
    messages=(),
    image_query_files={},
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
