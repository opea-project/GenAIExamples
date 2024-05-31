# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain.prompts import PromptTemplate

prompt_template = """
    ### System: Please translate the following {language_from} codes into {language_to} codes.

    ### Original codes:
    '''{language_from}

    {source_code}

    '''

    ### Translated codes:
"""
codetrans_prompt_template = PromptTemplate.from_template(prompt_template)
