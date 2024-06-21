# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain.prompts import PromptTemplate

prompt_template = """
    Translate this from {language_from} to {language_to}:

    {language_from}:
    {source_language}

    {language_to}:
"""
translation_prompt_template = PromptTemplate.from_template(prompt_template)
