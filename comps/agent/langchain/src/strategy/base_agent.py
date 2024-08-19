# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from ..tools import get_tools_descriptions
from ..utils import setup_llm


class BaseAgent:
    def __init__(self, args) -> None:
        self.llm_endpoint = setup_llm(args)
        self.tools_descriptions = get_tools_descriptions(args.tools)
        self.app = None
        print(self.tools_descriptions)

    def compile(self):
        pass

    def execute(self, state: dict):
        pass

    def non_streaming_run(self, query, config):
        raise NotImplementedError
