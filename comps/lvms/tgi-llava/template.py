# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class ChatTemplate:

    @staticmethod
    def generate_multimodal_rag_on_videos_prompt(question: str, context: str, has_image: bool = False):

        if has_image:
            template = """The transcript associated with the image is '{context}'. {question}"""
        else:
            template = (
                """Refer to the following results obtained from the local knowledge base: '{context}'. {question}"""
            )

        return template.format(context=context, question=question)
