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
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_milvus.vectorstores import Milvus
from langchain_text_splitters import HTMLHeaderTextSplitter
from pyspark import SparkConf, SparkContext

from comps import DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    get_file_structure,
    get_separators,
    get_tables_result,
    parse_html,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

# workaround notes: cp comps/dataprep/utils.py ./milvus/utils.py
# from utils import document_loader, get_tables_result, parse_html
index_params = {"index_type": "FLAT", "metric_type": "IP", "params": {}}
partition_field_name = "filename"
upload_folder = "./uploaded_files/"


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


def ingest_data_to_milvus(doc_path: DocPath):
    """Ingest document to Milvus."""
    path = doc_path.path
    file_name = path.split("/")[-1]
    print(f"[ ingest data ] Parsing document {path}, file name: {file_name}.")

    if path.endswith(".html"):
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=doc_path.chunk_size, chunk_overlap=100, add_start_index=True, separators=get_separators()
        )

    content = document_loader(path)
    chunks = text_splitter.split_text(content)
    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)
        chunks = chunks + table_chunks
    print("[ ingest data ] Done preprocessing. Created ", len(chunks), " chunks of the original pdf")

    # Create vectorstore
    if MOSEC_EMBEDDING_ENDPOINT:
        # create embeddings using MOSEC endpoint service
        print(
            f"[ ingest data ] MOSEC_EMBEDDING_ENDPOINT:{MOSEC_EMBEDDING_ENDPOINT}, MOSEC_EMBEDDING_MODEL:{MOSEC_EMBEDDING_MODEL}"
        )
        embedder = MosecEmbeddings(model=MOSEC_EMBEDDING_MODEL)
    elif TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        print(f"[ ingest data ] TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
        embedder = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        print(f"[ ingest data ] Local TEI_EMBEDDING_MODEL:{TEI_EMBEDDING_MODEL}")
        embedder = HuggingFaceBgeEmbeddings(model_name=TEI_EMBEDDING_MODEL)

    # insert documents to Milvus
    insert_docs = []
    for chunk in chunks:
        insert_docs.append(Document(page_content=chunk, metadata={partition_field_name: file_name}))

    try:
        _ = Milvus.from_documents(
            insert_docs,
            embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
            partition_key_field=partition_field_name,
        )
    except Exception as e:
        print(f"[ ingest data ] fail to ingest data into Milvus. error: {e}")
        return False

    print(f"[ ingest data ] Docs ingested from {path} to Milvus collection {COLLECTION_NAME}.")

    return True


async def ingest_link_to_milvus(link_list: List[str]):
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

    for link in link_list:
        content = parse_html([link])[0][0]
        print(f"[ ingest link ] link: {link} content: {content}")
        encoded_link = encode_filename(link)
        save_path = upload_folder + encoded_link + ".txt"
        print(f"[ ingest link ] save_path: {save_path}")
        await save_content_to_local_disk(save_path, content)

        document = Document(page_content=content, metadata={partition_field_name: encoded_link + ".txt"})
        _ = Milvus.from_documents(
            document,
            embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
            partition_key_field=partition_field_name,
        )


@register_microservice(name="opea_service@prepare_doc_milvus", endpoint="/v1/dataprep", host="0.0.0.0", port=6010)
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
        uploaded_files = []
        for file in files:
            save_path = upload_folder + file.filename
            await save_content_to_local_disk(save_path, file)
            uploaded_files.append(save_path)
            print(f"Successfully saved file {save_path}")

        def process_files_wrapper(files):
            if not isinstance(files, list):
                files = [files]
            for file in files:
                assert ingest_data_to_milvus(
                    DocPath(
                        path=file,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        process_table=process_table,
                        table_strategy=table_strategy,
                    )
                )

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
            await ingest_link_to_milvus(link_list)
            print(f"Successfully saved link list {link_list}")
            return {"status": 200, "message": "Data preparation succeeded"}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_milvus_file", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6011
)
async def rag_get_file_structure():
    print("[ dataprep - get file ] start to get file structure")

    if not Path(upload_folder).exists():
        print("No file uploaded, return empty list.")
        return []

    file_content = get_file_structure(upload_folder)
    return file_content


def delete_all_data(my_milvus):
    print("[ delete ] deleting all data in milvus")
    my_milvus.delete(expr="pk >= 0")
    my_milvus.col.flush()
    print("[ delete ] delete success: all data")


def delete_by_partition_field(my_milvus, partition_field):
    print(f"[ delete ] deleting {partition_field_name} {partition_field}")
    pks = my_milvus.get_pks(f'{partition_field_name} == "{partition_field}"')
    print(f"[ delete ] target pks: {pks}")
    res = my_milvus.delete(pks)
    my_milvus.col.flush()
    print(f"[ delete ] delete success: {res}")


@register_microservice(
    name="opea_service@prepare_doc_milvus_del", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6012
)
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - file/link path (e.g. /path/to/file.txt)
        - "all": delete all files uploaded
    """
    # create embedder obj
    if MOSEC_EMBEDDING_ENDPOINT:
        # create embeddings using MOSEC endpoint service
        print(
            f"[ dataprep - del ] MOSEC_EMBEDDING_ENDPOINT:{MOSEC_EMBEDDING_ENDPOINT},MOSEC_EMBEDDING_MODEL:{MOSEC_EMBEDDING_MODEL}"
        )
        embedder = MosecEmbeddings(model=MOSEC_EMBEDDING_MODEL)
    elif TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        print(f"[ dataprep - del ] TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
        embedder = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        print(f"[ dataprep - del ] Local TEI_EMBEDDING_MODEL:{TEI_EMBEDDING_MODEL}")
        embedder = HuggingFaceBgeEmbeddings(model_name=TEI_EMBEDDING_MODEL)

    # define Milvus obj
    my_milvus = Milvus(
        embedding_function=embedder,
        collection_name=COLLECTION_NAME,
        connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
        index_params=index_params,
        auto_id=True,
    )

    # delete all uploaded files
    if file_path == "all":
        print("[ dataprep - del ] deleting all files")
        delete_all_data(my_milvus)
        remove_folder_with_ignore(upload_folder)
        print("[ dataprep - del ] successfully delete all files.")
        create_upload_folder(upload_folder)
        return {"status": True}

    encode_file_name = encode_filename(file_path)
    delete_path = Path(upload_folder + "/" + encode_file_name)
    print(f"[dataprep - del] delete_path: {delete_path}")

    # partially delete files
    if delete_path.exists():
        # file
        if delete_path.is_file():
            print(f"[dataprep - del] deleting file {encode_file_name}")
            try:
                delete_by_partition_field(my_milvus, encode_file_name)
                delete_path.unlink()
                print(f"[dataprep - del] file {encode_file_name} deleted")
                return {"status": True}
            except Exception as e:
                print(f"[dataprep - del] fail to delete file {delete_path}: {e}")
                return {"status": False}
        # folder
        else:
            print("[dataprep - del] delete folder is not supported for now.")
            return {"status": False}
    else:
        raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    opea_microservices["opea_service@prepare_doc_milvus"].start()
    opea_microservices["opea_service@prepare_doc_milvus_file"].start()
    opea_microservices["opea_service@prepare_doc_milvus_del"].start()
