# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any, List, Optional

from edgecraftrag.base import BaseComponent
from pydantic import model_serializer


class Knowledge(BaseComponent):
    file_paths: Optional[List[str]] = []
    file_map: Optional[List[str]] = {}
    description: Optional[str] = "None"
    comp_type: str = "knowledge"
    active: bool

    def _update_file_names(self) -> None:
        self.file_map = {os.path.basename(path): path for path in self.file_paths if path is not None}

    def add_file_path(self, file_path: str) -> bool:
        if file_path not in self.file_paths:
            self.file_paths.append(file_path)
            self._update_file_names()
            return True
        return False

    def remove_file_path(self, file_path: str) -> bool:
        if file_path in self.file_paths:
            self.file_paths.remove(file_path)
            self._update_file_names()
            return True
        return False

    def get_file_paths(self) -> List[str]:
        return self.file_paths

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "name": self.name,
            "comp_type": self.comp_type,
            "file_map": self.file_map,
            "description": self.description,
            "active": self.active,
        }
        return set
