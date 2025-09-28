# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from typing import Any, Callable, List, Optional

from edgecraftrag.base import BaseMgr
from edgecraftrag.components.data import File
from llama_index.core.schema import Document


class FilelMgr(BaseMgr):

    def __init__(self):
        super().__init__()

    def add_text(self, text: str):
        file = File(file_name="text", content=text)
        self.add(file)
        return file.documents

    def add_files(self, docs: Any, docs_name: str = "default"):
        if not isinstance(docs, list):
            docs = [docs]

        input_docs = []
        for doc in docs:
            if not os.path.exists(doc):
                continue

            if os.path.isfile(doc):
                files = [doc]
            elif os.path.isdir(doc):
                files = [os.path.join(root, f) for root, _, files in os.walk(doc) for f in files]
            else:
                continue

            if not files:
                continue

            for file_path in files:
                file = File(file_path=file_path)
                self.append(file, docs_name)
                input_docs.extend(file.documents)
        return input_docs

    def get_file_by_name(self, docs_name: str = "default", file_path: str = None):
        for name, files in self.components.items():
            if docs_name == name:
                for file in files:
                    if file_path == file.documents[0].metadata["file_path"]:
                        return file.documents
        return None

    def get_kb_files_by_name(self, docs_name: str = "default"):
        file_docs = []
        for name, files in self.components.items():
            if name == docs_name:
                return files
        return file_docs

    def get_all_docs(self) -> List[Document]:
        all_docs = {}
        for doc_name, files in self.components.items():
            all_docs[doc_name] = files
        return all_docs

    def update_file(self, name):
        file = self.get_file_by_name_or_id(name)
        if file:
            self.remove(file.idx)
            self.add_files(docs=name)
            return True
        else:
            return False

    def del_kb_file(self, docs_name: str = "default"):
        files = self.get_kb_files_by_name(docs_name)
        if files:
            self.remove(docs_name)

    def del_file(self, docs_name: str = "default", file_path: str = None):
        files = self.get_file_by_name(docs_name, file_path)
        docs_list = []
        for docs_file in files:
            docs_list.append(docs_file.id_)
        files = self.get_kb_files_by_name(docs_name)
        for docs_file in files:
            if file_path == docs_file.documents[0].metadata["file_path"]:
                self.components[docs_name].remove(docs_file)
                return docs_list
        return None
