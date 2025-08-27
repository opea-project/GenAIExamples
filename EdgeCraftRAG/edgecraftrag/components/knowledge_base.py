# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os, json
from typing import Any, List, Optional, Dict, Union

from edgecraftrag.base import BaseComponent
from pydantic import model_serializer


class Knowledge(BaseComponent):
    file_paths: Optional[List[str]] = []
    file_map: Optional[List[str]] = {}
    description: Optional[str] = "None"
    comp_type: Optional[str] = "knowledge"
    experience_active: Optional[bool] = False if comp_type == "knowledge" else True
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

    def ensure_file_exists(self):
        dir_path = os.path.dirname(self.file_paths[0])
        os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(self.file_paths[0]):
            with open(self.file_paths[0], 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def get_all_experience(self) -> List[Dict]:
        experinence_file = "/home/user/ui_cache/configs/experience_dir/experience.json"
        if experinence_file not in self.file_paths:
            self.file_paths.append(experinence_file)
        if not os.path.isfile(self.file_paths[0]):
            self.ensure_file_exists()
        with open(self.file_paths[0], 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_experience_by_question(self, question: str) -> Optional[Dict]:
        for item in self.get_all_experience():
            if item.get('question') == question:
                return item
        return None

    def add_multiple_experiences(self, experiences: List[Dict[str, Union[str, List[str]]]], flag: bool = True) -> List[Dict]:
        all_experiences = self.get_all_experience()
        result = []
        for exp in experiences:
            question = exp.get('question')
            if not question:
                raise ValueError("Must exist when uploading question")
            content = exp.get('content', [])
            found = False
            for item in all_experiences:
                if item['question'] == question:
                    if flag:
                        item['content'].extend([c for c in content if c not in item['content']])
                    else:
                        item['content'] = content
                    result.append(item)
                    found = True
                    break
            if not found:
                new_item = {'question': question, 'content': content}
                all_experiences.append(new_item)
                result.append(new_item)
        with open(self.file_paths[0], 'w', encoding='utf-8') as f:
            json.dump(all_experiences, f, ensure_ascii=False, indent=4)
        return result

    def delete_experience(self, question: str) -> bool:
        items = self.get_all_experience()
        remaining_items = [item for item in items if item.get('question') != question]
        if len(remaining_items) == len(items):
            return False
        with open(self.file_paths[0], 'w', encoding='utf-8') as f:
            json.dump(remaining_items, f, ensure_ascii=False, indent=4)
        return True

    def clear_experiences(self) -> bool:
        all_experiences = self.get_all_experience()
        with open(self.file_paths[0], 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return True

    def update_experience(self, question: str, content: List[str]) -> Optional[Dict]:
        items = self.get_all_experience()
        for i, item in enumerate(items):
            if item.get('question') == question:
                updated_item = {'question': question, 'content': content}
                items[i] = updated_item
                with open(self.file_paths[0], 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
                return updated_item
        return None

    def add_experiences_from_file(self, file_path: str, flag: bool = False) -> List[Dict]:
        if not file_path.endswith('.json'):
            raise ValueError("File upload type error")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                experiences = json.load(f)
            if not isinstance(experiences, list):
                raise ValueError("The contents of the file must be a list")
            return self.add_multiple_experiences(experiences=experiences, flag=flag)
        except json.JSONDecodeError as e:
            raise ValueError(f"File parsing failure")
        except Exception as e:
            raise RuntimeError(f"File Error")

    def calculate_totals(self):
        if self.comp_type == "knowledge":
            total = len(self.file_paths)
        elif self.comp_type == "experience":
            total = len(self.get_all_experience())
        else:
            total = None
        return total

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
            "experience_active": self.experience_active,
            "total": self.calculate_totals()
        }
        return set
