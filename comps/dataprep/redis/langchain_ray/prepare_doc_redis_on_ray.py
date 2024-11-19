# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import pathlib
import shutil
import sys
from pathlib import Path
from typing import Callable, List, Optional, Union

import pandas as pd
from config import EMBED_MODEL, INDEX_NAME, REDIS_URL, TIMEOUT_SECONDS
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Redis

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../../")
sys.path.append(comps_path)
import hashlib
import timeit
from typing import Any, Dict, Iterator

import pyarrow
import ray
from ray.data.block import Block
from ray.data.datasource import FileBasedDatasource
from tqdm import tqdm

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    Timer,
    create_upload_folder,
    document_loader,
    encode_filename,
    get_file_structure,
    get_separators,
    parse_html_new,
    remove_folder_with_ignore,
    save_content_to_local_disk,
    timeout,
)

logger = CustomLogger("prepare_doc_redis")
logflag = os.getenv("LOGFLAG", False)

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
debug = False
upload_folder = "./uploaded_files/"


def prepare_env(enable_ray=False, pip_requirements=None):
    if enable_ray:
        import ray

        if ray.is_initialized():
            ray.shutdown()
        if pip_requirements is not None:
            ray.init(runtime_env={"pip": pip_requirements, "env_vars": {"PYTHONPATH": comps_path}})
        else:
            ray.init(runtime_env={"env_vars": {"PYTHONPATH": comps_path}})


def generate_log_name(file_list):
    file_set = f"{sorted(file_list)}"
    # if logflag:
    # logger.info(f"file_set: {file_set}")
    md5_str = hashlib.md5(file_set.encode(), usedforsecurity=False).hexdigest()
    return f"status/status_{md5_str}.log"


def get_failable_with_time(callable):
    def failable_callable(*args, **kwargs):
        start_time = timeit.default_timer()
        try:
            content = callable(*args, **kwargs)
            error = None
        except Exception as e:
            content = None
            error = str(e)
        end_time = timeit.default_timer()
        return content, error, f"{'%.3f' % (end_time - start_time)}"

    return failable_callable


def get_max_cpus(total_num_tasks):
    num_cpus_available = os.cpu_count()
    num_cpus_per_task = num_cpus_available // total_num_tasks
    if num_cpus_per_task == 0:
        return 8
    return num_cpus_per_task


def save_logs(log_name, data):
    df = pd.DataFrame.from_records(data)
    try:
        dir_path = os.path.dirname(log_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        df.to_csv(log_name)
    except:
        pass
    return df


def generate_ray_dataset(file_paths, dataloader_callable, lazy_mode=True, num_cpus=20):
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


def ray_execute(ds, log_name):
    with Timer(f"execute with Ray, status log: {log_name}"):
        ret_with_status = ds.take_all()
        df = save_logs(log_name, ret_with_status)
        ret = df.to_dict(orient="records")
    return ret


@timeout(seconds=TIMEOUT_SECONDS)
def data_to_redis_ray(data):
    content = data["data"]
    if content is None:
        return {
            "filename": data["filename"],
            "content": content,
            "status": "failed",
            "num_chunks": -1,
            "error": data["error"],
            "read_time": data["read_time"],
            "elaspe_time": "0.0 secs",
        }

    decorated_callable = get_failable_with_time(data_to_redis)
    num_chunks, error, elapse_time = decorated_callable(content)
    status = "success" if not error else "failed"
    if not debug:
        content = None
    return {
        "filename": data["filename"],
        "content": content,
        "status": status,
        "num_chunks": num_chunks,
        "error": error,
        "read_time": data["read_time"],
        "elaspe_time": f"{elapse_time} secs",
    }


def data_to_redis(data):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, chunk_overlap=100, add_start_index=True, separators=get_separators(), is_separator_regex=False
    )
    if isinstance(data, list):
        chunks = data
    elif isinstance(data, str):
        chunks = text_splitter.split_text(data)
    else:
        raise TypeError("The content must be either a list or a string.")

    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        _ = Redis.from_texts(
            texts=batch_texts,
            embedding=embedder,
            index_name=INDEX_NAME,
            redis_url=REDIS_URL,
        )
        # if logflag:
        # logger.info(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")
    return num_chunks


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


def ingest_data_to_redis(file_list: List[DocPath], enable_ray=False, num_cpus=20):
    """Ingest document to Redis."""
    file_list = [f.path for f in file_list]

    if enable_ray:
        log_name = generate_log_name(file_list)
        ds = generate_ray_dataset(file_list, document_loader, lazy_mode=True, num_cpus=num_cpus)
        ds = ds.map(data_to_redis_ray, num_cpus=num_cpus)
        return ray_execute(ds, log_name)
    else:
        for file in tqdm(file_list, total=len(file_list)):
            with Timer(f"read document {file}."):
                data = document_loader(file)
            with Timer(f"ingest document {file} to Redis."):
                data_to_redis(data)
        return True


def ingest_link_to_redis(link_list: List[str], enable_ray=False, num_cpus=20):
    link_list = [str(f) for f in link_list]

    def _parse_html(link):
        data = parse_html_new([link], chunk_size=1500, chunk_overlap=100)
        return data[0][0]

    if enable_ray:
        log_name = generate_log_name(link_list)
        ds = generate_ray_dataset(link_list, _parse_html, lazy_mode=True, num_cpus=num_cpus)
        ds = ds.map(data_to_redis_ray, num_cpus=num_cpus)
        return ray_execute(ds, log_name)
    else:
        for link in tqdm(link_list, total=len(link_list)):
            with Timer(f"read document {link}."):
                data = _parse_html(link)
            if logflag:
                logger.info("content is: ", data)
            with Timer(f"ingest document {link} to Redis."):
                data_to_redis(data)
        return True


@register_microservice(name="opea_service@prepare_doc_redis", endpoint="/v1/dataprep", host="0.0.0.0", port=6007)
async def ingest_documents(files: List[UploadFile] = File(None), link_list: str = Form(None)):
    if logflag:
        logger.info(files)
        logger.info(link_list)
    if files and link_list:
        raise HTTPException(status_code=400, detail="Provide either a file or a string list, not both.")

    if not files and not link_list:
        raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")

    saved_path_list = []
    if files:
        try:
            if not isinstance(files, list):
                files = [files]
            if not os.path.exists(upload_folder):
                Path(upload_folder).mkdir(parents=True, exist_ok=True)

            # TODO: use ray to parallelize the file saving
            for file in files:
                save_path = upload_folder + file.filename
                await save_content_to_local_disk(save_path, file)
                saved_path_list.append(DocPath(path=save_path))

            if len(saved_path_list) <= 10:
                enable_ray = False
            else:
                enable_ray = True
            prepare_env(enable_ray=enable_ray)
            num_cpus = get_max_cpus(len(saved_path_list))
            if logflag:
                logger.info(f"per task num_cpus: {num_cpus}")
            ret = ingest_data_to_redis(saved_path_list, enable_ray=enable_ray, num_cpus=num_cpus)
            result = {"status": 200, "message": f"Data preparation succeeded. ret msg is {ret}"}
            if logflag:
                logger.info(result)
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An error occurred: {e}")

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail="link_list should be a list.")
            if len(link_list) <= 10:
                enable_ray = False
            else:
                enable_ray = True
            prepare_env(enable_ray=enable_ray)
            num_cpus = get_max_cpus(len(link_list))
            if logflag:
                logger.info(f"per task num_cpus: {num_cpus}")
            ret = ingest_link_to_redis(link_list, enable_ray=enable_ray, num_cpus=num_cpus)
            result = {"status": 200, "message": f"Data preparation succeeded. ret msg is {ret}"}
            if logflag:
                logger.info(result)
            return result
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


@register_microservice(
    name="opea_service@prepare_doc_redis_file", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6008
)
async def rag_get_file_structure():
    if logflag:
        logger.info("[ get_file_structure] ")

    if not Path(upload_folder).exists():
        if logflag:
            logger.info("No file uploaded, return empty list.")
        return []

    file_content = get_file_structure(upload_folder)
    if logflag:
        logger.info(file_content)
    return file_content


@register_microservice(
    name="opea_service@prepare_doc_redis_del", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6009
)
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - specific file path (e.g. /path/to/file.txt)
        - folder path (e.g. /path/to/folder)
        - "all": delete all files uploaded
    """
    if logflag:
        logger.info(file_path)
    # delete all uploaded files
    if file_path == "all":
        if logflag:
            logger.info("[dataprep - del] delete all files")
        remove_folder_with_ignore(upload_folder)
        if logflag:
            logger.info("[dataprep - del] successfully delete all files.")
        create_upload_folder(upload_folder)
        if logflag:
            logger.info({"status": True})
        return {"status": True}

    delete_path = Path(upload_folder + "/" + encode_filename(file_path))
    if logflag:
        logger.info(f"[dataprep - del] delete_path: {delete_path}")

    # partially delete files/folders
    if delete_path.exists():
        # delete file
        if delete_path.is_file():
            try:
                delete_path.unlink()
            except Exception as e:
                if logflag:
                    logger.info(f"[dataprep - del] fail to delete file {delete_path}: {e}")
                    logger.info({"status": False})
                return {"status": False}
        # delete folder
        else:
            try:
                shutil.rmtree(delete_path)
            except Exception as e:
                if logflag:
                    logger.info(f"[dataprep - del] fail to delete folder {delete_path}: {e}")
                    logger.info({"status": False})
                return {"status": False}
        if logflag:
            logger.info({"status": True})
        return {"status": True}
    else:
        raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")


if __name__ == "__main__":

    opea_microservices["opea_service@prepare_doc_redis"].start()
    opea_microservices["opea_service@prepare_doc_redis_file"].start()
