# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from jinja2 import BaseLoader, Environment

PROMPT = open("utils/prompt_template.jinja2").read().strip()


def get_formatted_prompt(scene, prompt, history):
    env = Environment(loader=BaseLoader())
    template = env.from_string(PROMPT)
    return template.render(scene=scene, prompt=prompt, history=history)
