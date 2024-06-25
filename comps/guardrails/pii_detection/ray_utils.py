# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Union

import pyarrow
import ray
from ray.data.block import Block
from ray.data.datasource import FileBasedDatasource
from tqdm import tqdm
from utils import Timer, get_failable_with_time, save_logs, timeout


class RayDataLoader(FileBasedDatasource):
    def __init__(
        self,
        paths: Union[str, List[str]],
        dataloader_callable: Optional[Callable],
        document_ld_args: Optional[Dict[str, Any]] = None,
        **file_based_datasource_kwargs,
    ):
        super().__init__(paths, **file_based_datasource_kwargs)
        self.dataloader_callable = dataloader_callable
        self.args = document_ld_args or {}

    def _read_stream(self, f: "pyarrow.NativeFile", path: str) -> Iterator[Block]:
        from ray.data._internal.arrow_block import ArrowBlockBuilder

        builder = ArrowBlockBuilder()
        path = f"{path}"
        data, error, read_time = self.dataloader_callable(path)
        item = {"data": data, "filename": path, "error": error, "read_time": f"{read_time} secs"}
        builder.add(item)
        yield builder.build()


def rayds_initialization(file_paths, dataloader_callable, lazy_mode=True, num_cpus=20):
    if dataloader_callable is None:
        text_list = [{"data": data, "filename": data[:50], "error": None, "read_time": "0 secs"} for data in file_paths]
        return ray.data.from_items(text_list)

    decorated_dataloader_callable = get_failable_with_time(dataloader_callable)
    if lazy_mode:
        if num_cpus is None:
            return ray.data.read_datasource(RayDataLoader(file_paths, decorated_dataloader_callable))
        else:
            return ray.data.read_datasource(
                RayDataLoader(file_paths, decorated_dataloader_callable), ray_remote_args={"num_cpus": num_cpus}
            )
    else:
        data = []
        for file in tqdm(file_paths, total=len(file_paths)):
            content, error, elapse_time = decorated_dataloader_callable(file)
            item = {"data": content, "filename": file, "error": error, "read_time": f"{elapse_time} secs"}
            data.append(item)
        return ray.data.from_items(data)


def ray_runner_initialization(func, debug=False):
    @timeout(600)
    def ray_runner(data):
        content = data["data"]
        if content is None:
            return {
                "filename": data["filename"],
                "content": content,
                "status": "failed",
                "ret": -1,
                "error": data["error"],
                "read_time": data["read_time"],
                "elaspe_time": "0.0 secs",
            }

        decorated_callable = get_failable_with_time(func)
        ret, error, elapse_time = decorated_callable(content)
        status = "success" if not error else "failed"
        if not debug:
            content = None
        return {
            "filename": data["filename"],
            "content": content,
            "status": status,
            "ret": ret,
            "error": error,
            "read_time": data["read_time"],
            "elaspe_time": f"{elapse_time} secs",
        }

    return ray_runner


def ray_execute(ds, log_name):
    with Timer(f"execute with Ray, status log: {log_name}"):
        ret_with_status = ds.take_all()
        df = save_logs(log_name, ret_with_status)
        ret = df["ret"].to_list()
    return ret
