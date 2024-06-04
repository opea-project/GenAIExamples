# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from jinja2 import BaseLoader, Environment, select_autoescape


def get_formatted_prompt(scene, prompt, history):
    env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"]))
    template = env.from_string(PROMPT)
