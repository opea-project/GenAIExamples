# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import io
import os
from pathlib import Path
from typing import Iterator, List, Optional

from docx.text.paragraph import Paragraph
from edgecraftrag.base import InferenceType
from edgecraftrag.env import IMG_OUTPUT_DIR
from PIL import Image as Img
from transformers import AutoTokenizer
from unstructured.documents.elements import ElementMetadata, Image
from unstructured.partition.docx import DocxPartitionerOptions

DEFAULT_TEMPLATE = """You are an AI assistant. Your task is to learn from the following context. Then answer the user's question based on what you learned from the context but not your own knowledge.

{context}

Pay attention to your formatting of response. If you need to reference content from context, try to keep the formatting.
Try to summarize from the context, do some reasoning before response, then response. Make sure your response is logically sound and self-consistent.

"""


class DocxParagraphPicturePartitioner:
    @classmethod
    def iter_elements(cls, paragraph: Paragraph, opts: DocxPartitionerOptions) -> Iterator[Image]:
        imgs = paragraph._element.xpath(".//pic:pic")
        if imgs:
            for img in imgs:
                embed = img.xpath(".//a:blip/@r:embed")[0]
                related_part = opts.document.part.related_parts[embed]
                image_blob = related_part.blob
                image = Img.open(io.BytesIO(image_blob))
                image_path = os.path.join(IMG_OUTPUT_DIR, str(embed) + related_part.sha1 + ".png")
                image.save(image_path)
                element_metadata = ElementMetadata(image_path=image_path)
            yield Image(text="IMAGE", metadata=element_metadata)


def get_prompt_template(model_path, prompt_content=None, template_path=None, enable_think=False):
    if prompt_content is not None:
        template = prompt_content
    elif template_path is not None:
        # Safely load the template only if it is inside /templates (or other safe root)
        safe_root = "/templates"
        normalized_path = os.path.normpath(os.path.join(safe_root, template_path))
        if not normalized_path.startswith(safe_root):
            raise ValueError("Template path is outside of the allowed directory.")
        if not os.path.exists(normalized_path):
            raise FileNotFoundError("Template file does not exist.")
        template = Path(normalized_path).read_text(encoding=None)
    else:
        template = DEFAULT_TEMPLATE
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    messages = [{"role": "system", "content": template}, {"role": "user", "content": "\n{input}\n"}]
    prompt_template = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=enable_think,  # Switches between thinking and non-thinking modes. Default is True.
    )
    return template, prompt_template


def serialize_node_with_score(node_with_score):
    # relationships is not serializable
    # No need for this information right now
    node_with_score.node.relationships = {}
    return {
        "node": node_with_score.node.__dict__,
        "score": node_with_score.score.item() if hasattr(node_with_score.score, "item") else node_with_score.score,
    }


def serialize_contexts(contexts):
    return {key: [serialize_node_with_score(node) for node in nodes] for key, nodes in contexts.items()}


async def stream_generator(string: str):
    for token in iter(string):
        yield token
        await asyncio.sleep(0)


async def chain_async_generators(gen_list: List):
    for stream in gen_list:
        async for token in stream:
            yield token
