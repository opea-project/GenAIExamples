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

    def add_files(self, docs: Any):
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
                self.add(file)
                input_docs.extend(file.documents)

        return input_docs

    def get_file_by_name_or_id(self, name: str):
        for _, file in self.components.items():
            if file.name == name or file.idx == name:
                return file
        return None

    def get_files(self):
        return [file for _, file in self.components.items()]

    def get_all_docs(self) -> List[Document]:
        all_docs = []
        for _, file in self.components.items():
            all_docs.extend(file.documents)
        return all_docs

    def get_docs_by_file(self, name) -> List[Document]:
        file = self.get_file_by_name_or_id(name)
        return file.documents if file else []

    def del_file(self, name):
        file = self.get_file_by_name_or_id(name)
        if file:
            self.remove(file.idx)
            return True
        else:
            return False

    def update_file(self, name):
        file = self.get_file_by_name_or_id(name)
        if file:
            self.remove(file.idx)
            self.add_files(docs=name)
            return True
        else:
            return False
