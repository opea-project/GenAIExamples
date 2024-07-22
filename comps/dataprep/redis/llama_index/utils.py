# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
import urllib.parse
from pathlib import Path
from typing import Dict, List, Union


def create_upload_folder(upload_path):
    if not os.path.exists(upload_path):
        Path(upload_path).mkdir(parents=True, exist_ok=True)


def encode_filename(filename):
    return urllib.parse.quote(filename, safe="")


def decode_filename(encoded_filename):
    return urllib.parse.unquote(encoded_filename)


def get_file_structure(root_path: str, parent_path: str = "") -> List[Dict[str, Union[str, List]]]:
    result = []
    for path in os.listdir(root_path):
        complete_path = parent_path + "/" + path if parent_path else path
        file_path = root_path + "/" + path
        p = Path(file_path)
        # append file into result
        if p.is_file():
            file_dict = {
                "name": decode_filename(path),
                "id": decode_filename(complete_path),
                "type": "File",
                "parent": "",
            }
            result.append(file_dict)
        else:
            # append folder and inner files/folders into result using recursive function
            folder_dict = {
                "name": decode_filename(path),
                "id": decode_filename(complete_path),
                "type": "Directory",
                "children": get_file_structure(file_path, complete_path),
                "parent": "",
            }
            result.append(folder_dict)

    return result


def remove_folder_with_ignore(folder_path: str, except_patterns: List = []):
    """Remove the specific folder, and ignore some files/folders.

    :param folder_path: file path to delete
    :param except_patterns: files/folder name to ignore
    """
    print(f"except patterns: {except_patterns}")
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            # delete files except ones that match patterns
            file_path = os.path.join(root, name)
            if except_patterns != [] and any(pattern in file_path for pattern in except_patterns):
                continue
            os.remove(file_path)

        # delete empty folder
        for name in dirs:
            dir_path = os.path.join(root, name)
            # delete folders except ones that match patterns
            if except_patterns != [] and any(pattern in dir_path for pattern in except_patterns):
                continue
            if not os.listdir(dir_path):
                os.rmdir(dir_path)


async def save_content_to_local_disk(save_path: str, content):
    save_path = Path(save_path)
    try:
        if isinstance(content, str):
            with open(save_path, "w", encoding="utf-8") as file:
                file.write(content)
        else:
            with save_path.open("wb") as fout:
                content = await content.read()
                fout.write(content)
    except Exception as e:
        print(f"Write file failed. Exception: {e}")
        raise Exception(status_code=500, detail=f"Write file {save_path} failed. Exception: {e}")
