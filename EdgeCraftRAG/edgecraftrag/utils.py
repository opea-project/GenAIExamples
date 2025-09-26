# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import io
import os
from pathlib import Path
from typing import Iterator, List, Optional

from docx.text.paragraph import Paragraph
from edgecraftrag.base import InferenceType
from edgecraftrag.context import ctx
from PIL import Image as Img
from transformers import AutoTokenizer
from unstructured.documents.elements import ElementMetadata, Image
from unstructured.partition.docx import DocxPartitionerOptions

UI_DIRECTORY = os.getenv("TMPFILE_PATH", "/home/user/ui_cache")
IMG_OUTPUT_DIR = os.path.join(UI_DIRECTORY, "pic")
os.makedirs(IMG_OUTPUT_DIR, exist_ok=True)

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
        template = Path(template_path).read_text(encoding=None)
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
    return prompt_template


def serialize_node_with_score(node_with_score):
    return {
        "node": node_with_score.node.__dict__,
        "score": node_with_score.score.item() if hasattr(node_with_score.score, "item") else node_with_score.score,
    }


def serialize_contexts(contexts):
    return {key: [serialize_node_with_score(node) for node in nodes] for key, nodes in contexts.items()}


def compare_mappings(new_dict, old_dict):
    added_files = {}
    deleted_files = {}
    for key in set(new_dict) - set(old_dict):
        added_files[key] = new_dict[key]
    for key in set(old_dict) - set(new_dict):
        deleted_files[key] = old_dict[key]
    for key in set(new_dict) & set(old_dict):
        new_files = new_dict[key]
        old_files = old_dict[key]
        added = {name: new_files[name] for name in set(new_files) - set(old_files)}
        if added:
            added_files[key] = added
        deleted = {name: old_files[name] for name in set(old_files) - set(new_files)}
        if deleted:
            deleted_files[key] = deleted
    return added_files, deleted_files


_history_map = {}
_current_session_id: Optional[str] = None


def set_current_session(session_id: str) -> None:
    global _current_session_id
    _current_session_id = session_id if session_id not in (None, "", "None") else "default_session"


def get_current_session() -> Optional[str]:
    return _current_session_id


def clear_history() -> None:
    session_id = get_current_session()
    if session_id in _history_map:
        _history_map[session_id] = []


def save_history(message: str) -> str:
    session_id = get_current_session()
    _history_map.setdefault(session_id, []).append(f"content: {message}")
    return "History appended successfully"


def concat_history(message: str) -> str:
    max_token = 6000
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if active_pl.generator.inference_type == InferenceType.VLLM:
        vllm_max_len = int(os.getenv("MAX_MODEL_LEN", "10240"))
        if vllm_max_len > 5000:
            max_token = vllm_max_len - 1024

    history_id = get_current_session()
    history_id_list = _history_map.get(history_id, [])
    str_message = get_recent_chat_rounds(history_id_list)
    _history_map.setdefault(history_id, []).append(f"user: {message}")
    return str_message[-max_token:] if len(str_message) > max_token else str_message


def get_recent_chat_rounds(history_id_list: List[str]) -> str:
    history_num = int(os.getenv("CHAT_HISTORY_ROUND", "0"))
    actual_rounds = min(history_num, len(history_id_list) // 2)
    if actual_rounds <= 0:
        return ""
    start_index = max(0, len(history_id_list) - (actual_rounds * 2 + 1))
    recent_history = history_id_list[start_index:]
    return "".join(recent_history)
