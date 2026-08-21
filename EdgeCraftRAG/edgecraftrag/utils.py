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


def resolve_prompt_template_path(template_path: str) -> Path:
    if not template_path:
        raise ValueError("Template path is empty.")

    # Support both container path and source-tree path.
    allowed_roots = [Path("/templates"), Path(__file__).resolve().parent / "prompt_template"]
    requested = Path(template_path).expanduser()

    if requested.is_absolute():
        normalized = requested.resolve()
        if not any(str(normalized).startswith(str(root.resolve())) for root in allowed_roots):
            raise ValueError("Template path is outside of the allowed directory.")
        if not normalized.exists():
            raise FileNotFoundError(f"Template file does not exist: {normalized}")
        return normalized

    for root in allowed_roots:
        candidate = (root / requested).resolve()
        if str(candidate).startswith(str(root.resolve())) and candidate.exists():
            return candidate

    searched = [str((root / requested).resolve()) for root in allowed_roots]
    raise FileNotFoundError(f"Template file does not exist. Tried: {searched}")


def _resolve_model_path(model_path: str) -> str:
    if not model_path:
        return model_path

    path_obj = Path(model_path)
    if path_obj.is_absolute() and path_obj.exists():
        return str(path_obj)

    candidates = [
        Path.cwd() / path_obj,
        Path(__file__).resolve().parents[1] / path_obj,
        Path(__file__).resolve().parents[2] / path_obj,
    ]

    model_env = os.getenv("MODEL_PATH")
    container_model_root = Path("/home/user/models")
    if model_env:
        model_root = Path(model_env).expanduser().resolve()
        model_parts = list(path_obj.parts)
        if model_parts[:1] == ["."]:
            model_parts = model_parts[1:]
        if model_parts[:1] == ["models"]:
            model_parts = model_parts[1:]
        if model_parts:
            candidates.append(model_root / Path(*model_parts))
            candidates.append(model_root / path_obj.name)

    model_parts = list(path_obj.parts)
    if model_parts[:1] == ["."]:
        model_parts = model_parts[1:]
    if model_parts[:1] == ["models"]:
        model_parts = model_parts[1:]
    if model_parts:
        candidates.append(container_model_root / Path(*model_parts))
        candidates.append(container_model_root / path_obj.name)

    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            continue
        if resolved.exists():
            return str(resolved)

    return model_path


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


def get_prompt_template(model_path, prompt_content=None, template_path=None, enable_think=False, use_chat=False):
    model_path = _resolve_model_path(model_path)
    if prompt_content is not None:
        template = prompt_content
    elif template_path is not None:
        normalized_path = resolve_prompt_template_path(template_path)
        template = normalized_path.read_text(encoding=None)
    else:
        template = DEFAULT_TEMPLATE
    if use_chat:
        return template, template
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=os.path.exists(model_path))
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
