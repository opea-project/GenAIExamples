# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class ChatTemplate:

    @staticmethod
    def generate_multimodal_rag_on_videos_prompt(question: str, context: str):
        template = """The transcript associated with the image is '{context}'. {question}"""
        return template.format(context=context, question=question)
