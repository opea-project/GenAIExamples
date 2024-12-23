# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Any, List, Optional

from edgecraftrag.base import BaseComponent, CompType, FileType
from llama_index.core.schema import Document
from pydantic import BaseModel, Field, model_serializer


class File(BaseComponent):
    file_path: str = Field(default="")
    comp_subtype: str = Field(default="")
    documents: List[Document] = Field(default=[])

    def __init__(self, file_name: Optional[str] = None, file_path: Optional[str] = None, content: Optional[str] = None):
        super().__init__(comp_type=CompType.FILE)

        if not file_name and not file_path:
            raise ValueError("File name or path must be provided")

        _path = Path(file_path) if file_path else None
        if file_name:
            self.name = file_name
        else:
            self.name = _path.name
        self.file_path = _path
        self.comp_subtype = FileType.TEXT
        if _path and _path.exists():
            self.documents.extend(convert_file_to_documents(_path))
        if content:
            self.documents.extend(convert_text_to_documents(content))

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {
            "file_name": self.name,
            "file_id": self.idx,
            "file_type": self.comp_subtype,
            "file_path": str(self.file_path),
            "docs_count": len(self.documents),
        }
        return set


def convert_text_to_documents(text) -> List[Document]:
    return [Document(text=text, metadata={"file_name": "text"})]


def convert_file_to_documents(file_path) -> List[Document]:
    from llama_index.core import SimpleDirectoryReader

    supported_exts = [".pdf", ".txt", ".doc", ".docx", ".pptx", ".ppt", ".csv", ".md", ".html", ".rst"]
    if file_path.is_dir():
        docs = SimpleDirectoryReader(input_dir=file_path, recursive=True, required_exts=supported_exts).load_data()
    elif file_path.is_file():
        docs = SimpleDirectoryReader(input_files=[file_path], required_exts=supported_exts).load_data()
    else:
        docs = []

    return docs
