# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import sys

import requests

sys.path.append("..")
import os

from edgecraftrag import api_schema

PIPELINE_SERVICE_HOST_IP = os.getenv("PIPELINE_SERVICE_HOST_IP", "127.0.0.1")
PIPELINE_SERVICE_PORT = int(os.getenv("PIPELINE_SERVICE_PORT", 16010))
server_addr = f"http://{PIPELINE_SERVICE_HOST_IP}:{PIPELINE_SERVICE_PORT}"


def get_current_pipelines():
    res = requests.get(f"{server_addr}/v1/settings/pipelines", proxies={"http": None})
    pls = []
    for pl in res.json():
        if pl["status"]["active"]:
            pls.append((pl["idx"], pl["name"] + " (active)"))
        else:
            pls.append((pl["idx"], pl["name"]))
    return pls


def get_pipeline(name):
    res = requests.get(f"{server_addr}/v1/settings/pipelines/{name}", proxies={"http": None})
    return res.json()


def create_update_pipeline(
    name,
    active,
    node_parser,
    chunk_size,
    chunk_overlap,
    indexer,
    retriever,
    vector_search_top_k,
    postprocessor,
    generator,
    llm_id,
    llm_device,
    llm_weights,
    embedding_id,
    embedding_device,
    rerank_id,
    rerank_device,
):
    req_dict = api_schema.PipelineCreateIn(
        name=name,
        active=active,
        node_parser=api_schema.NodeParserIn(
            parser_type=node_parser, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        ),
        indexer=api_schema.IndexerIn(
            indexer_type=indexer,
            embedding_model=api_schema.ModelIn(
                model_id=embedding_id,
                # TODO: remove hardcoding
                model_path="./bge_ov_embedding",
                device=embedding_device,
            ),
        ),
        retriever=api_schema.RetrieverIn(retriever_type=retriever, retriever_topk=vector_search_top_k),
        postprocessor=[
            api_schema.PostProcessorIn(
                processor_type=postprocessor[0],
                reranker_model=api_schema.ModelIn(
                    model_id=rerank_id,
                    # TODO: remove hardcoding
                    model_path="./bge_ov_reranker",
                    device=rerank_device,
                ),
            )
        ],
        generator=api_schema.GeneratorIn(
            # TODO: remove hardcoding
            prompt_path="./edgecraftrag/prompt_template/default_prompt.txt",
            model=api_schema.ModelIn(
                model_id=llm_id,
                # TODO: remove hardcoding
                model_path="./models/qwen2-7b-instruct/INT4_compressed_weights",
                device=llm_device,
            ),
        ),
    )
    # hard code only for test
    print(req_dict)
    res = requests.post(f"{server_addr}/v1/settings/pipelines", json=req_dict.dict(), proxies={"http": None})
    return res.text


def activate_pipeline(name):
    active_dict = {"active": "True"}
    res = requests.patch(f"{server_addr}/v1/settings/pipelines/{name}", json=active_dict, proxies={"http": None})
    status = False
    restext = f"Activate pipeline {name} failed."
    if res.ok:
        status = True
        restext = f"Activate pipeline {name} successfully."
    return restext, status


def create_vectordb(docs, spliter, vector_db):
    req_dict = api_schema.FilesIn(local_paths=docs)
    res = requests.post(f"{server_addr}/v1/data/files", json=req_dict.dict(), proxies={"http": None})
    return res.text


def get_files():
    res = requests.get(f"{server_addr}/v1/data/files", proxies={"http": None})
    files = []
    for file in res.json():
        files.append((file["file_name"], file["file_id"]))
    return files


def delete_file(file_name_or_id):
    res = requests.delete(f"{server_addr}/v1/data/files/{file_name_or_id}", proxies={"http": None})
    return res.text
