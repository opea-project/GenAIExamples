#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Redis
from rag_redis.config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, REDIS_URL
from PIL import Image
import numpy as np
import io


def pdf_loader(file_path):
    try:
        import fitz  # noqa:F401
        import easyocr
    except ImportError:
        raise ImportError(
            "`PyMuPDF` or 'easyocr' package is not found, please install it with "
            "`pip install pymupdf or pip install easyocr.`"
        )

    doc = fitz.open(file_path)
    reader = easyocr.Reader(['en'])
    result =''
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pagetext = page.get_text().strip()
        if pagetext:
            result=result+pagetext
        if len(doc.get_page_images(i)) > 0 :
            for img in doc.get_page_images(i):
                if img:
                    pageimg=''
                    xref = img[0]
                    img_data = doc.extract_image(xref)
                    img_bytes = img_data['image']
                    pil_image = Image.open(io.BytesIO(img_bytes))
                    img = np.array(pil_image)
                    img_result = reader.readtext(img, paragraph=True, detail=0)
                    pageimg=pageimg + ', '.join(img_result).strip()
                    if pageimg.endswith('!') or pageimg.endswith('?') or pageimg.endswith('.'):
                        pass
                    else:
                        pageimg=pageimg+'.'
                result=result+pageimg
    return result

def ingest_documents():
    """
    Ingest PDF to Redis from the data/ directory that
    contains Intel manuals.
    """
    # Load list of pdfs
    company_name = "Intel"
    data_path = "data_intel/"
    doc_path = [os.path.join(data_path, file) for file in os.listdir(data_path)][0]

    print("Parsing Intel architecture manuals", doc_path)  # noqa: T201

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, chunk_overlap=100, add_start_index=True
    )
    content = pdf_loader(doc_path)
    chunks = text_splitter.split_text(content)

    print("Done preprocessing. Created", len(chunks), "chunks of the original pdf")  # noqa: T201
    # Create vectorstore
    embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    _ = Redis.from_texts(
        # appending this little bit can sometimes help with semantic retrieval
        # especially with multiple companies
        texts=[f"Company: {company_name}. " + chunk for chunk in chunks],
        embedding=embedder,
        index_name=INDEX_NAME,
        index_schema=INDEX_SCHEMA,
        redis_url=REDIS_URL,
    )


if __name__ == "__main__":
    ingest_documents()
