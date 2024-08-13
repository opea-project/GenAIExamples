# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import psycopg2
from config import CHUNK_OVERLAP, CHUNK_SIZE, EMBED_MODEL, INDEX_NAME, PG_CONNECTION_STRING
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import PGVector
from langsmith import traceable

from comps import DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    get_file_structure,
    get_separators,
    parse_html,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
upload_folder = "./uploaded_files/"


async def save_file_to_local_disk(save_path: str, file):
    save_path = Path(save_path)
    with save_path.open("wb") as fout:
        try:
            content = await file.read()
            fout.write(content)
        except Exception as e:
            print(f"Write file failed. Exception: {e}")
            raise HTTPException(status_code=500, detail=f"Write file {save_path} failed. Exception: {e}")


def delete_embeddings(doc_name):
    """Get all ids from a vectorstore."""
    try:
        result = urlparse(PG_CONNECTION_STRING)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port

        connection = psycopg2.connect(database=database, user=username, password=password, host=hostname, port=port)

        # Create a cursor object to execute SQL queries
        print(f"Deleting {doc_name} from vectorstore")

        cur = connection.cursor()
        if doc_name == "all":
            cur.execute(
                "DELETE FROM langchain_pg_collection lpe WHERE lpe.name = %(index_name)s",
                {"index_name": INDEX_NAME},
            )
        else:
            cur.execute(
                "DELETE  FROM langchain_pg_embedding lpe WHERE lpe.uuid in (SELECT lpc.uuid\
                    FROM langchain_pg_embedding lpc where lpc.cmetadata ->> 'doc_name' = %(doc_name)s)",
                {"doc_name": doc_name},
            )

        connection.commit()  # commit the transaction
        cur.close()

        return True

    except psycopg2.Error as e:
        print(f"Error deleting document from vectorstore: {e}")
        return False

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def ingest_doc_to_pgvector(doc_path: DocPath):
    """Ingest document to PGVector."""
    doc_path = doc_path.path
    print(f"Parsing document {doc_path}.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True, separators=get_separators()
    )
    content = document_loader(doc_path)
    chunks = text_splitter.split_text(content)
    print("Done preprocessing. Created ", len(chunks), " chunks of the original pdf")
    print("PG Connection", PG_CONNECTION_STRING)
    metadata = [dict({"doc_name": str(doc_path)})]

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

        _ = PGVector.from_texts(
            texts=batch_texts,
            embedding=embedder,
            metadatas=metadata,
            collection_name=INDEX_NAME,
            connection_string=PG_CONNECTION_STRING,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")
    return True


async def ingest_link_to_pgvector(link_list: List[str]):
    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True, separators=get_separators()
    )

    for link in link_list:
        texts = []
        content = parse_html([link])[0][0]
        print(f"[ ingest link ] link: {link} content: {content}")
        encoded_link = encode_filename(link)
        save_path = upload_folder + encoded_link + ".txt"
        doc_path = upload_folder + link + ".txt"
        print(f"[ ingest link ] save_path: {save_path}")
        await save_content_to_local_disk(save_path, content)
        metadata = [dict({"doc_name": str(doc_path)})]

        chunks = text_splitter.split_text(content)

        batch_size = 32
        num_chunks = len(chunks)
        for i in range(0, num_chunks, batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_texts = batch_chunks

            _ = PGVector.from_texts(
                texts=batch_texts,
                embedding=embedder,
                metadatas=metadata,
                collection_name=INDEX_NAME,
                connection_string=PG_CONNECTION_STRING,
            )
            print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")

    return True


@register_microservice(
    name="opea_service@prepare_doc_pgvector",
    endpoint="/v1/dataprep",
    host="0.0.0.0",
    port=6007,
)
@traceable(run_type="tool")
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None), link_list: Optional[str] = Form(None)
):
    print(f"files:{files}")
    print(f"link_list:{link_list}")
    if files and link_list:
        raise HTTPException(status_code=400, detail="Provide either a file or a string list, not both.")

    if files:
        if not isinstance(files, list):
            files = [files]

        if not os.path.exists(upload_folder):
            Path(upload_folder).mkdir(parents=True, exist_ok=True)
        for file in files:
            save_path = upload_folder + file.filename
            await save_file_to_local_disk(save_path, file)

            ingest_doc_to_pgvector(DocPath(path=save_path))
            print(f"Successfully saved file {save_path}")
        return {"status": 200, "message": "Data preparation succeeded"}

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail="link_list should be a list.")
            await ingest_link_to_pgvector(link_list)
            print(f"Successfully saved link list {link_list}")
            return {"status": 200, "message": "Data preparation succeeded"}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_pgvector", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6007
)
@traceable(run_type="tool")
async def rag_get_file_structure():
    print("[ dataprep - get file ] start to get file structure")

    if not Path(upload_folder).exists():
        print("No file uploaded, return empty list.")
        return []

    file_content = get_file_structure(upload_folder)
    return file_content


@register_microservice(
    name="opea_service@prepare_doc_pgvector", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6007
)
@traceable(run_type="tool")
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - specific file path (e.g. /path/to/file.txt)
        - folder path (e.g. /path/to/folder)
        - "all": delete all files uploaded
    """
    if file_path == "all":
        print("[dataprep - del] delete all files")
        remove_folder_with_ignore(upload_folder)
        assert delete_embeddings(file_path)
        print("[dataprep - del] successfully delete all files.")
        create_upload_folder(upload_folder)
        return {"status": True}

    delete_path = Path(upload_folder + "/" + encode_filename(file_path))
    doc_path = upload_folder + file_path
    print(f"[dataprep - del] delete_path: {delete_path}")

    # partially delete files/folders
    if delete_path.exists():
        # delete file
        if delete_path.is_file():
            try:
                assert delete_embeddings(doc_path)
                delete_path.unlink()
            except Exception as e:
                print(f"[dataprep - del] fail to delete file {delete_path}: {e}")
                return {"status": False}
        # delete folder
        else:
            print("[dataprep - del] delete folder is not supported for now.")
            return {"status": False}
        return {"status": True}
    else:
        raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    opea_microservices["opea_service@prepare_doc_pgvector"].start()
