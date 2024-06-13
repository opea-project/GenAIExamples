#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import argparse
import io
import os

import numpy as np
from config import COLLECTION_NAME, EMBED_ENDPOINT, EMBED_MODEL, MILVUS_HOST, MILVUS_PORT
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain_milvus.vectorstores import Milvus
from PIL import Image


def pdf_loader(file_path):
    try:
        import easyocr
        import fitz
    except ImportError:
        raise ImportError(
            "`PyMuPDF` or 'easyocr' package is not found, please install it with "
            "`pip install pymupdf or pip install easyocr.`"
        )

    doc = fitz.open(file_path)
    reader = easyocr.Reader(["en"])
    result = ""
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pagetext = page.get_text().strip()
        if pagetext:
            result = result + pagetext
        if len(doc.get_page_images(i)) > 0:
            for img in doc.get_page_images(i):
                if img:
                    pageimg = ""
                    xref = img[0]
                    img_data = doc.extract_image(xref)
                    img_bytes = img_data["image"]
                    pil_image = Image.open(io.BytesIO(img_bytes))
                    img = np.array(pil_image)
                    img_result = reader.readtext(img, paragraph=True, detail=0)
                    pageimg = pageimg + ", ".join(img_result).strip()
                    if pageimg.endswith("!") or pageimg.endswith("?") or pageimg.endswith("."):
                        pass
                    else:
                        pageimg = pageimg + "."
                result = result + pageimg
    return result


def ingest_documents(folder_path, tag):
    """Ingest PDF to Milvus from a directory."""
    # Load list of pdfs
    doc_path = [os.path.join(folder_path, file) for file in os.listdir(folder_path)][0]

    print("Parsing...", doc_path)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100, add_start_index=True)
    content = pdf_loader(doc_path)
    chunks = text_splitter.split_text(content)

    print("Done preprocessing. Created ", len(chunks), " chunks of the original pdf")
    # Create vectorstore
    if EMBED_ENDPOINT:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=EMBED_ENDPOINT)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = [f"Tag: {tag}. " + chunk for chunk in batch_chunks]

        _ = Milvus.from_texts(
            texts=batch_texts,
            embedding=embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents from a specified folder with a tag")
    parser.add_argument("folder_path", type=str, help="Path to the folder containing documents")
    parser.add_argument("--tag", type=str, default="", help="Tag to be used as an identifier")

    args = parser.parse_args()
    ingest_documents(args.folder_path, args.tag)
