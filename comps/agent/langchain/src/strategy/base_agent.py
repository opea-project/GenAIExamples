# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

from ..tools import get_tools_descriptions
from ..utils import adapt_custom_prompt, setup_chat_model


class BaseAgent:
    def __init__(self, args, local_vars=None, **kwargs) -> None:
        self.llm = setup_chat_model(args)
        self.tools_descriptions = get_tools_descriptions(args.tools)
        self.app = None
        self.memory = None
        self.id = f"assistant_{self.__class__.__name__}_{uuid4()}"
        self.args = args
        adapt_custom_prompt(local_vars, kwargs.get("custom_prompt"))
        print(self.tools_descriptions)

    @property
    def is_vllm(self):
        return self.args.llm_engine == "vllm"

    @property
    def is_tgi(self):
        return self.args.llm_engine == "tgi"

    @property
    def is_openai(self):
        return self.args.llm_engine == "openai"

    def compile(self):
        pass

    def execute(self, state: dict):
        pass

    def non_streaming_run(self, query, config):
        raise NotImplementedError
