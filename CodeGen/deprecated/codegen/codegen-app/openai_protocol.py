#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#
"""Code source from FastChat's OpenAI protocol:

https://github.com/lm-sys/FastChat/blob/main/fastchat/protocol/openai_api_protocol.py
"""
import time
from typing import Any, List, Optional, Union

import shortuuid

# pylint: disable=E0611
from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    prompt: Union[str, List[Any]]
    device: Optional[str] = "cpu"
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    top_k: Optional[int] = 1
    repetition_penalty: Optional[float] = 1.0
    max_new_tokens: Optional[int] = 128
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{shortuuid.random()}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    response: str
