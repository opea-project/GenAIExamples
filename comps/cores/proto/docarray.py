# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional

import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import AudioDoc
from docarray.typing import AudioUrl
from pydantic import Field, conlist


class TextDoc(BaseDoc):
    text: str


class Base64ByteStrDoc(BaseDoc):
    byte_str: str


class DocPath(BaseDoc):
    path: str


class EmbedDoc768(BaseDoc):
    text: str
    embedding: conlist(float, min_length=768, max_length=768)


class Audio2TextDoc(AudioDoc):
    url: Optional[AudioUrl] = Field(
        description="The path to the audio.",
        default=None,
    )
    model_name_or_path: Optional[str] = Field(
        description="The Whisper model name or path.",
        default="openai/whisper-small",
    )
    language: Optional[str] = Field(
        description="The language that Whisper prefer to detect.",
        default="auto",
    )


class EmbedDoc1024(BaseDoc):
    text: str
    embedding: conlist(float, min_length=1024, max_length=1024)


class SearchedDoc(BaseDoc):
    retrieved_docs: DocList[TextDoc]
    initial_query: str

    class Config:
        json_encoders = {np.ndarray: lambda x: x.tolist()}


class GeneratedDoc(BaseDoc):
    text: str
    prompt: str


class LLMParamsDoc(BaseDoc):
    query: str
    max_new_tokens: int = 1024
    top_k: int = 10
    top_p: float = 0.95
    typical_p: float = 0.95
    temperature: float = 0.01
    repetition_penalty: float = 1.03
    streaming: bool = True
