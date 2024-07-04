# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import uuid
from pathlib import Path
from typing import List, Optional, Union

from config import (
    COLLECTION_NAME,
    MILVUS_HOST,
    MILVUS_PORT,
    MOSEC_EMBEDDING_ENDPOINT,
    MOSEC_EMBEDDING_MODEL,
    TEI_EMBEDDING_ENDPOINT,
    TEI_EMBEDDING_MODEL,
)
from fastapi import File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings, OpenAIEmbeddings
from langchain_milvus.vectorstores import Milvus
from langchain_text_splitters import HTMLHeaderTextSplitter
from langsmith import traceable
from pyspark import SparkConf, SparkContext

from comps import DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import document_loader, get_tables_result, parse_html

# workaround notes: cp comps/dataprep/utils.py ./milvus/utils.py
# from utils import document_loader, get_tables_result, parse_html
index_params = {"index_type": "FLAT", "metric_type": "IP", "params": {}}


class MosecEmbeddings(OpenAIEmbeddings):
    def _get_len_safe_embeddings(
        self, texts: List[str], *, engine: str, chunk_size: Optional[int] = None
    ) -> List[List[float]]:
        _chunk_size = chunk_size or self.chunk_size
        batched_embeddings: List[List[float]] = []
        response = self.client.create(input=texts, **self._invocation_params)
        if not isinstance(response, dict):
            response = response.model_dump()
        batched_embeddings.extend(r["embedding"] for r in response["data"])

        _cached_empty_embedding: Optional[List[float]] = None

        def empty_embedding() -> List[float]:
            nonlocal _cached_empty_embedding
            if _cached_empty_embedding is None:
                average_embedded = self.client.create(input="", **self._invocation_params)
                if not isinstance(average_embedded, dict):
                    average_embedded = average_embedded.model_dump()
                _cached_empty_embedding = average_embedded["data"][0]["embedding"]
            return _cached_empty_embedding

        return [e if e is not None else empty_embedding() for e in batched_embeddings]


async def save_file_to_local_disk(save_path: str, file):
    save_path = Path(save_path)
    with save_path.open("wb") as fout:
        try:
            content = await file.read()
            fout.write(content)
        except Exception as e:
            print(f"Write file failed. Exception: {e}")
            raise HTTPException(status_code=500, detail=f"Write file {save_path} failed. Exception: {e}")


def ingest_data_to_milvus(doc_path: DocPath):
    """Ingest document to Milvus."""
    path = doc_path.path
    print(f"Parsing document {path}.")

    if path.endswith(".html"):
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=doc_path.chunk_size, chunk_overlap=100, add_start_index=True
        )

    content = document_loader(path)
    chunks = text_splitter.split_text(content)
    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)
        chunks = chunks + table_chunks
    print("Done preprocessing. Created ", len(chunks), " chunks of the original pdf")

    # Create vectorstore
    if MOSEC_EMBEDDING_ENDPOINT:
        # create embeddings using MOSEC endpoint service
        print(f"MOSEC_EMBEDDING_ENDPOINT:{MOSEC_EMBEDDING_ENDPOINT},MOSEC_EMBEDDING_MODEL:{MOSEC_EMBEDDING_MODEL}")
        embedder = MosecEmbeddings(model=MOSEC_EMBEDDING_MODEL)
    elif TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        print(f"TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
        embedder = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        print(f"Local TEI_EMBEDDING_MODEL:{TEI_EMBEDDING_MODEL}")
        embedder = HuggingFaceBgeEmbeddings(model_name=TEI_EMBEDDING_MODEL)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks
        _ = Milvus.from_texts(
            texts=batch_texts,
            embedding=embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
            index_params=index_params,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")

    return True


def ingest_link_to_milvus(link_list: List[str]):
    data_collection = parse_html(link_list)

    texts = []
    metadatas = []
    for data, meta in data_collection:
        doc_id = str(uuid.uuid4())
        metadata = {"source": meta, "identify_id": doc_id}
        texts.append(data)
        metadatas.append(metadata)

    # Create vectorstore
    if MOSEC_EMBEDDING_ENDPOINT:
        # create embeddings using MOSEC endpoint service
        print(f"MOSEC_EMBEDDING_ENDPOINT:{MOSEC_EMBEDDING_ENDPOINT},MOSEC_EMBEDDING_MODEL:{MOSEC_EMBEDDING_MODEL}")
        embedder = MosecEmbeddings(model=MOSEC_EMBEDDING_MODEL)
    elif TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        print(f"TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
        embedder = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        print(f"Local TEI_EMBEDDING_MODEL:{TEI_EMBEDDING_MODEL}")
        embedder = HuggingFaceBgeEmbeddings(model_name=TEI_EMBEDDING_MODEL)

    _ = Milvus.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embedder,
        collection_name=COLLECTION_NAME,
        connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
        index_params=index_params,
    )


@register_microservice(name="opea_service@prepare_doc_milvus", endpoint="/v1/dataprep", host="0.0.0.0", port=6010)
@traceable(run_type="tool")
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1500),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    print(f"files:{files}")
    print(f"link_list:{link_list}")
    if files and link_list:
        raise HTTPException(status_code=400, detail="Provide either a file or a string list, not both.")

    if files:
        if not isinstance(files, list):
            files = [files]
        upload_folder = "./uploaded_files/"
        if not os.path.exists(upload_folder):
            Path(upload_folder).mkdir(parents=True, exist_ok=True)
        uploaded_files = []
        for file in files:
            save_path = upload_folder + file.filename
            await save_file_to_local_disk(save_path, file)
            ingest_data_to_milvus(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                )
            )
            uploaded_files.append(save_path)
            print(f"Successfully saved file {save_path}")

        def process_files_wrapper(files):
            if not isinstance(files, list):
                files = [files]
            for file in files:
                ingest_data_to_milvus(DocPath(path=file, chunk_size=chunk_size, chunk_overlap=chunk_overlap))

        try:
            # Create a SparkContext
            conf = SparkConf().setAppName("Parallel-dataprep").setMaster("local[*]")
            sc = SparkContext(conf=conf)
            # Create an RDD with parallel processing
            parallel_num = min(len(uploaded_files), os.cpu_count())
            rdd = sc.parallelize(uploaded_files, parallel_num)
            # Perform a parallel operation
            rdd_trans = rdd.map(process_files_wrapper)
            rdd_trans.collect()
            # Stop the SparkContext
            sc.stop()
        except:
            # Stop the SparkContext
            sc.stop()
        return {"status": 200, "message": "Data preparation succeeded"}

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail="link_list should be a list.")
            ingest_link_to_milvus(link_list)
            print(f"Successfully saved link list {link_list}")
            return {"status": 200, "message": "Data preparation succeeded"}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


if __name__ == "__main__":
    opea_microservices["opea_service@prepare_doc_milvus"].start()
