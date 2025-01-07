# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# for test


import json
import os
from pathlib import Path
from typing import List, Optional, Union

from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_milvus.vectorstores import Milvus
from langchain_text_splitters import HTMLHeaderTextSplitter

from comps import CustomLogger, DocPath, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.dataprep.src.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    format_file_list,
    get_separators,
    get_tables_result,
    parse_html_new,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

from .config import COLLECTION_NAME, INDEX_PARAMS, LOCAL_EMBEDDING_MODEL, MILVUS_URI, TEI_EMBEDDING_ENDPOINT

logger = CustomLogger("milvus_dataprep")
logflag = os.getenv("LOGFLAG", False)
partition_field_name = "filename"
upload_folder = "./uploaded_files/"


def ingest_chunks_to_milvus(embeddings, file_name: str, chunks: List):
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
                connection_args={"uri": MILVUS_URI},
                partition_key_field=partition_field_name,
            )
        except Exception as e:
            if logflag:
                logger.info(f"[ ingest chunks ] fail to ingest chunks into Milvus. error: {e}")
            raise HTTPException(status_code=500, detail=f"Fail to store chunks of file {file_name}.")

    if logflag:
        logger.info(f"[ ingest chunks ] Docs ingested file {file_name} to Milvus collection {COLLECTION_NAME}.")

    return True


def ingest_data_to_milvus(doc_path: DocPath, embeddings):
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

    return ingest_chunks_to_milvus(embeddings, file_name, chunks)


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


@OpeaComponentRegistry.register("OPEA_DATAPREP_MILVUS")
class OpeaMilvusDataprep(OpeaComponent):
    """A specialized dataprep component derived from OpeaComponent for milvus dataprep services.

    Attributes:
        client (Milvus): An instance of the milvus client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.DATAPREP.name.lower(), description, config)
        self.embedder = self._initialize_embedder()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaMilvusDataprep health check failed.")

    def _initialize_embedder(self):
        if logflag:
            logger.info("[ initialize embedder ] initializing milvus embedder...")
        if TEI_EMBEDDING_ENDPOINT:
            # create embeddings using TEI endpoint service
            if logflag:
                logger.info(f"[ milvus embedding ] TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
            embeddings = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
        else:
            # create embeddings using local embedding model
            if logflag:
                logger.info(f"[ milvus embedding ] LOCAL_EMBEDDING_MODEL:{LOCAL_EMBEDDING_MODEL}")
            embeddings = HuggingFaceBgeEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
        return embeddings

    def check_health(self) -> bool:
        """Checks the health of the dataprep service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ health check ] start to check health of milvus")
        try:
            client = Milvus(
                embedding_function=self.embedder,
                collection_name=COLLECTION_NAME,
                connection_args={"uri": MILVUS_URI},
                index_params=INDEX_PARAMS,
                auto_id=True,
            )
            _ = client.client.list_collections()
            if logflag:
                logger.info("[ health check ] Successfully connected to Milvus!")
            return True
        except Exception as e:
            logger.info(f"[ health check ] Failed to connect to Milvus: {e}")
            return False

    def invoke(self, *args, **kwargs):
        pass

    async def ingest_files(
        self,
        files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
        link_list: Optional[str] = Form(None),
        chunk_size: int = Form(1500),
        chunk_overlap: int = Form(100),
        process_table: bool = Form(False),
        table_strategy: str = Form("fast"),
    ):
        """Ingest files/links content into milvus database.

        Save in the format of vector[], the vector length depends on the emedding model type.
        Returns '{"status": 200, "message": "Data preparation succeeded"}' if successful.
        Args:
            files (Union[UploadFile, List[UploadFile]], optional): A file or a list of files to be ingested. Defaults to File(None).
            link_list (str, optional): A list of links to be ingested. Defaults to Form(None).
            chunk_size (int, optional): The size of the chunks to be split. Defaults to Form(1500).
            chunk_overlap (int, optional): The overlap between chunks. Defaults to Form(100).
            process_table (bool, optional): Whether to process tables in PDFs. Defaults to Form(False).
            table_strategy (str, optional): The strategy to process tables in PDFs. Defaults to Form("fast").
        """
        if logflag:
            logger.info(f"[ milvus ingest ] files:{files}")
            logger.info(f"[ milvus ingest ] link_list:{link_list}")

        my_milvus = Milvus(
            embedding_function=self.embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"uri": MILVUS_URI},
            index_params=INDEX_PARAMS,
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
                    self.embedder,
                )
                uploaded_files.append(save_path)
                if logflag:
                    logger.info(f"[ milvus ingest] Successfully saved file {save_path}")

            result = {"status": 200, "message": "Data preparation succeeded"}
            if logflag:
                logger.info(result)
            return result

        if link_list:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail=f"Link_list {link_list} should be a list.")
            for link in link_list:
                encoded_link = encode_filename(link)
                if logflag:
                    logger.info(f"[ milvus ingest] processing link {encoded_link}")

                # check whether the link file already exists
                if my_milvus.col:
                    try:
                        search_res = search_by_file(my_milvus.col, encoded_link + ".txt")
                    except Exception as e:
                        raise HTTPException(
                            status_code=500, detail=f"Failed when searching in Milvus db for link {link}."
                        )
                    if len(search_res) > 0:
                        if logflag:
                            logger.info(f"[ milvus ingest ] Link {link} already exists.")
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
                    self.embedder,
                )
            if logflag:
                logger.info(f"[ milvus ingest] Successfully saved link list {link_list}")
            return {"status": 200, "message": "Data preparation succeeded"}

        raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")

    async def get_files(self):
        """Get file structure from milvus database in the format of
        {
            "name": "File Name",
            "id": "File Name",
            "type": "File",
            "parent": "",
        }"""

        if logflag:
            logger.info("[ milvus get ] start to get file structure")

        my_milvus = Milvus(
            embedding_function=self.embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"uri": MILVUS_URI},
            index_params=INDEX_PARAMS,
            auto_id=True,
        )

        if not my_milvus.col:
            logger.info(f"[ milvus get ] collection {COLLECTION_NAME} does not exist.")
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
            logger.info(f"[ milvus get ] unique list from db: {unique_list}")

        # construct result file list in format
        file_list = format_file_list(unique_list)

        if logflag:
            logger.info(f"[ milvus get ] final file list: {file_list}")
        return file_list

    async def delete_files(self, file_path: str = Body(..., embed=True)):
        """Delete file according to `file_path`.

        `file_path`:
            - specific file path (e.g. /path/to/file.txt)
            - "all": delete all files uploaded
        """
        if logflag:
            logger.info(f"[ milvus delete ] delete files: {file_path}")

        my_milvus = Milvus(
            embedding_function=self.embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"uri": MILVUS_URI},
            index_params=INDEX_PARAMS,
            auto_id=True,
        )

        # delete all uploaded files
        if file_path == "all":

            delete_all_data(my_milvus)

            # delete files on local disk
            try:
                remove_folder_with_ignore(upload_folder)
            except Exception as e:
                if logflag:
                    logger.info(f"[ milvus delete ] {e}. Fail to delete {upload_folder}.")
                raise HTTPException(status_code=500, detail=f"Fail to delete {upload_folder}.")

            if logflag:
                logger.info("[ milvus delete ] successfully delete all files.")

            create_upload_folder(upload_folder)
            if logflag:
                logger.info("[ milvus delete ] new upload folder created.")
            return {"status": True}

        encode_file_name = encode_filename(file_path)
        delete_path = Path(upload_folder + "/" + encode_file_name)
        if logflag:
            logger.info(f"[ milvus delete ] delete_path: {delete_path}")

        # partially delete files
        if delete_path.exists():

            # TODO: check existence before delete

            # delete file
            if delete_path.is_file():
                if logflag:
                    logger.info(f"[ milvus delete ] deleting file {encode_file_name}")
                try:
                    delete_by_partition_field(my_milvus, encode_file_name)
                except Exception as e:
                    if logflag:
                        logger.info(f"[ milvus delete ] fail to delete file {delete_path}: {e}")
                    return {"status": False}
                delete_path.unlink()
                if logflag:
                    logger.info(f"[ milvus delete ] file {file_path} deleted")
                return {"status": True}

            # delete folder
            else:
                if logflag:
                    logger.info(f"[ milvus delete ] delete folder {file_path} is not supported for now.")
                raise HTTPException(status_code=404, detail=f"Delete folder {file_path} is not supported for now.")
        else:
            raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")
