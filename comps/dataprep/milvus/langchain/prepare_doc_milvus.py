# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
from typing import List, Optional, Union

from config import (
    COLLECTION_NAME,
    LOCAL_EMBEDDING_MODEL,
    MILVUS_HOST,
    MILVUS_PORT,
    MOSEC_EMBEDDING_ENDPOINT,
    MOSEC_EMBEDDING_MODEL,
    TEI_EMBEDDING_ENDPOINT,
)
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_milvus.vectorstores import Milvus
from langchain_text_splitters import HTMLHeaderTextSplitter

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    decode_filename,
    document_loader,
    encode_filename,
    get_separators,
    get_tables_result,
    parse_html_new,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

logger = CustomLogger("prepare_doc_milvus")
logflag = os.getenv("LOGFLAG", False)

# workaround notes: cp comps/dataprep/utils.py ./milvus/utils.py
index_params = {"index_type": "FLAT", "metric_type": "IP", "params": {}}
partition_field_name = "filename"
upload_folder = "./uploaded_files/"
milvus_uri = f"http://{MILVUS_HOST}:{MILVUS_PORT}"


class MosecEmbeddings(OpenAIEmbeddings):
    def _get_len_safe_embeddings(
        self, texts: List[str], *, engine: str, chunk_size: Optional[int] = None
    ) -> List[List[float]]:
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


def ingest_chunks_to_milvus(file_name: str, chunks: List):
    if logflag:
        logger.info(f"[ ingest chunks ] file name: {file_name}")

    # insert documents to Milvus
    insert_docs = []
    for chunk in chunks:
        insert_docs.append(Document(page_content=chunk, metadata={partition_field_name: file_name}))

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)

    for i in range(0, num_chunks, batch_size):
        if logflag:
            logger.info(f"[ ingest chunks ] Current batch: {i}")
        batch_docs = insert_docs[i : i + batch_size]

        try:
            _ = Milvus.from_documents(
                batch_docs,
                embeddings,
                collection_name=COLLECTION_NAME,
                connection_args={"uri": milvus_uri},
                partition_key_field=partition_field_name,
            )
        except Exception as e:
            if logflag:
                logger.info(f"[ ingest chunks ] fail to ingest chunks into Milvus. error: {e}")
            raise HTTPException(status_code=500, detail=f"Fail to store chunks of file {file_name}.")

    if logflag:
        logger.info(f"[ ingest chunks ] Docs ingested file {file_name} to Milvus collection {COLLECTION_NAME}.")

    return True


def ingest_data_to_milvus(doc_path: DocPath):
    """Ingest document to Milvus."""
    path = doc_path.path
    file_name = path.split("/")[-1]
    if logflag:
        logger.info(f"[ ingest data ] Parsing document {path}, file name: {file_name}.")

    if path.endswith(".html"):
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=doc_path.chunk_size,
            chunk_overlap=doc_path.chunk_overlap,
            add_start_index=True,
            separators=get_separators(),
        )

    content = document_loader(path)

    if logflag:
        logger.info("[ ingest data ] file content loaded")

    structured_types = [".xlsx", ".csv", ".json", "jsonl"]
    _, ext = os.path.splitext(path)

    if ext in structured_types:
        chunks = content
    else:
        chunks = text_splitter.split_text(content)

    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)
        chunks = chunks + table_chunks
    if logflag:
        logger.info(f"[ ingest data ] Done preprocessing. Created {len(chunks)} chunks of the original file.")

    return ingest_chunks_to_milvus(file_name, chunks)


def search_by_file(collection, file_name):
    query = f"{partition_field_name} == '{file_name}'"
    results = collection.query(
        expr=query,
        output_fields=[partition_field_name, "pk"],
    )
    if logflag:
        logger.info(f"[ search by file ] searched by {file_name}")
        logger.info(f"[ search by file ] {len(results)} results: {results}")
    return results


def search_all(collection):
    results = collection.query(expr="pk >= 0", output_fields=[partition_field_name, "pk"])
    if logflag:
        logger.info(f"[ search all ] {len(results)} results: {results}")
    return results


def delete_all_data(my_milvus):
    if logflag:
        logger.info("[ delete all ] deleting all data in milvus")
    if my_milvus.col:
        my_milvus.col.drop()
    if logflag:
        logger.info("[ delete all ] delete success: all data")


def delete_by_partition_field(my_milvus, partition_field):
    if logflag:
        logger.info(f"[ delete partition ] deleting {partition_field_name} {partition_field}")
    pks = my_milvus.get_pks(f'{partition_field_name} == "{partition_field}"')
    if logflag:
        logger.info(f"[ delete partition ] target pks: {pks}")
    res = my_milvus.delete(pks)
    my_milvus.col.flush()
    if logflag:
        logger.info(f"[ delete partition ] delete success: {res}")


@register_microservice(name="opea_service@prepare_doc_milvus", endpoint="/v1/dataprep", host="0.0.0.0", port=6010)
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    if logflag:
        logger.info(f"[ upload ] files:{files}")
        logger.info(f"[ upload ] link_list:{link_list}")

    if files and link_list:
        raise HTTPException(status_code=400, detail="Provide either a file or a string list, not both.")

    # define Milvus obj
    my_milvus = Milvus(
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        connection_args={"uri": milvus_uri},
        index_params=index_params,
        auto_id=True,
    )

    if files:
        if not isinstance(files, list):
            files = [files]
        uploaded_files = []

        for file in files:
            encode_file = encode_filename(file.filename)
            save_path = upload_folder + encode_file
            if logflag:
                logger.info(f"[ upload ] processing file {save_path}")

            if my_milvus.col:
                # check whether the file is already uploaded
                try:
                    search_res = search_by_file(my_milvus.col, encode_file)
                except Exception as e:
                    raise HTTPException(
                        status_code=500, detail=f"Failed when searching in Milvus db for file {file.filename}."
                    )
                if len(search_res) > 0:
                    if logflag:
                        logger.info(f"[ upload ] File {file.filename} already exists.")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Uploaded file {file.filename} already exists. Please change file name.",
                    )

            await save_content_to_local_disk(save_path, file)
            ingest_data_to_milvus(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                ),
            )
            uploaded_files.append(save_path)
            if logflag:
                logger.info(f"Saved file {save_path} into local disk.")

        # def process_files_wrapper(files):
        #     if not isinstance(files, list):
        #         files = [files]
        #     for file in files:
        #         encode_file = encode_filename(file.filename)
        #         save_path = upload_folder + encode_file
        #         ingest_data_to_milvus(
        #             DocPath(
        #                 path=save_path,
        #                 chunk_size=chunk_size,
        #                 chunk_overlap=chunk_overlap,
        #                 process_table=process_table,
        #                 table_strategy=table_strategy,
        #             ),
        #         )

        # try:
        #     # Create a SparkContext
        #     conf = SparkConf().setAppName("Parallel-dataprep").setMaster("local[*]")
        #     sc = SparkContext(conf=conf)
        #     # Create an RDD with parallel processing
        #     parallel_num = min(len(uploaded_files), os.cpu_count())
        #     rdd = sc.parallelize(uploaded_files, parallel_num)
        #     print(uploaded_files)
        #     # Perform a parallel operation
        #     rdd_trans = rdd.map(process_files_wrapper)
        #     rdd_trans.collect()
        #     # Stop the SparkContext
        #     sc.stop()
        # except:
        #     # Stop the SparkContext
        #     sc.stop()
        results = {"status": 200, "message": "Data preparation succeeded"}
        if logflag:
            logger.info(results)
        return results

    if link_list:
        link_list = json.loads(link_list)  # Parse JSON string to list
        if not isinstance(link_list, list):
            raise HTTPException(status_code=400, detail="link_list should be a list.")

        for link in link_list:
            encoded_link = encode_filename(link)
            if logflag:
                logger.info(f"[ upload ] processing link {encoded_link}")

            # check whether the link file already exists
            if my_milvus.col:
                try:
                    search_res = search_by_file(my_milvus.col, encoded_link + ".txt")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed when searching in Milvus db for link {link}.")
                if len(search_res) > 0:
                    if logflag:
                        logger.info(f"[ upload ] Link {link} already exists.")
                    raise HTTPException(
                        status_code=400, detail=f"Uploaded link {link} already exists. Please change link."
                    )

            save_path = upload_folder + encoded_link + ".txt"
            content = parse_html_new([link], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            await save_content_to_local_disk(save_path, content)
            ingest_data_to_milvus(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                ),
            )
        if logflag:
            logger.info(f"[ upload ] Successfully saved link list {link_list}")
        return {"status": 200, "message": "Data preparation succeeded"}

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_milvus", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6010
)
async def rag_get_file_structure():
    if logflag:
        logger.info("[ get ] start to get file structure")

    # define Milvus obj
    my_milvus = Milvus(
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        connection_args={"uri": milvus_uri},
        index_params=index_params,
        auto_id=True,
    )

    # collection does not exist
    if not my_milvus.col:
        logger.info(f"[ get ] collection {COLLECTION_NAME} does not exist.")
        return []

    # get all files from db
    try:
        all_data = search_all(my_milvus.col)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed when searching in Milvus db for all files.")

    # return [] if no data in db
    if len(all_data) == 0:
        return []

    res_file = [res["filename"] for res in all_data]
    unique_list = list(set(res_file))
    if logflag:
        logger.info(f"[ get ] unique list from db: {unique_list}")

    # construct result file list in format
    file_list = []
    for file_name in unique_list:
        file_dict = {
            "name": decode_filename(file_name),
            "id": decode_filename(file_name),
            "type": "File",
            "parent": "",
        }
        file_list.append(file_dict)

    if logflag:
        logger.info(f"[ get ] final file list: {file_list}")
    return file_list


@register_microservice(
    name="opea_service@prepare_doc_milvus", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6010
)
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - file/link path (e.g. /path/to/file.txt)
        - "all": delete all files uploaded
    """
    if logflag:
        logger.info(file_path)

    # define Milvus obj
    my_milvus = Milvus(
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        connection_args={"uri": milvus_uri},
        index_params=index_params,
        auto_id=True,
    )

    # delete all uploaded files
    if file_path == "all":
        if logflag:
            logger.info("[ delete ] deleting all files")

        delete_all_data(my_milvus)

        # delete files on local disk
        try:
            remove_folder_with_ignore(upload_folder)
        except Exception as e:
            if logflag:
                logger.info(f"[ delete ] {e}. Fail to delete {upload_folder}.")
            raise HTTPException(status_code=500, detail=f"Fail to delete {upload_folder}.")

        if logflag:
            logger.info("[ delete ] successfully delete all files.")

        create_upload_folder(upload_folder)
        if logflag:
            logger.info("[ delete ] new upload folder created.")
        return {"status": True}

    encode_file_name = encode_filename(file_path)
    delete_path = Path(upload_folder + "/" + encode_file_name)
    if logflag:
        logger.info(f"[delete] delete_path: {delete_path}")

    # partially delete files
    if delete_path.exists():

        # TODO: check existence before delete

        # delete file
        if delete_path.is_file():
            if logflag:
                logger.info(f"[delete] deleting file {encode_file_name}")
            try:
                delete_by_partition_field(my_milvus, encode_file_name)
            except Exception as e:
                if logflag:
                    logger.info(f"[delete] fail to delete file {delete_path}: {e}")
                return {"status": False}
            delete_path.unlink()
            if logflag:
                logger.info(f"[delete] file {file_path} deleted")
            return {"status": True}

        # delete folder
        else:
            if logflag:
                logger.info(f"[delete] delete folder {file_path} is not supported for now.")
            raise HTTPException(status_code=404, detail=f"Delete folder {file_path} is not supported for now.")
    else:
        raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")


if __name__ == "__main__":
    create_upload_folder(upload_folder)

    # Create vectorstore
    if MOSEC_EMBEDDING_ENDPOINT:
        # create embeddings using MOSEC endpoint service
        if logflag:
            logger.info(
                f"[ prepare_doc_milvus ] MOSEC_EMBEDDING_ENDPOINT:{MOSEC_EMBEDDING_ENDPOINT}, MOSEC_EMBEDDING_MODEL:{MOSEC_EMBEDDING_MODEL}"
            )
        embeddings = MosecEmbeddings(model=MOSEC_EMBEDDING_MODEL)
    elif TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        if logflag:
            logger.info(f"[ prepare_doc_milvus ] TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
        embeddings = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        if logflag:
            logger.info(f"[ prepare_doc_milvus ] LOCAL_EMBEDDING_MODEL:{LOCAL_EMBEDDING_MODEL}")
        embeddings = HuggingFaceBgeEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)

    opea_microservices["opea_service@prepare_doc_milvus"].start()
