#!/usr/bin/env python

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

import io
import os

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Qdrant
from PIL import Image
from rag_qdrant.config import COLLECTION_NAME, EMBED_MODEL, QDRANT_HOST, QDRANT_PORT, TEI_EMBEDDING_ENDPOINT


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


def ingest_documents():
    """Ingest PDF to Qdrant from the data/ directory that
    contains Edgar 10k filings data for Nike."""
    # Load list of pdfs
    company_name = "Nike"
    data_path = "data/"
    doc_path = [os.path.join(data_path, file) for file in os.listdir(data_path)][0]

    print("Parsing 10k filing doc for NIKE", doc_path)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100, add_start_index=True)
    content = pdf_loader(doc_path)
    chunks = text_splitter.split_text(content)

    print("Done preprocessing. Created ", len(chunks), " chunks of the original pdf")
    # Create vectorstore
    if TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = [f"Company: {company_name}. " + chunk for chunk in batch_chunks]

        _ = Qdrant.from_texts(
            texts=batch_texts,
            embedding=embedder,
            collection_name=COLLECTION_NAME,
            host=QDRANT_HOST,
            port=QDRANT_PORT,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")


if __name__ == "__main__":
    ingest_documents()
