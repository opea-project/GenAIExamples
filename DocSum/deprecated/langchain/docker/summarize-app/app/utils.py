#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import re
import uuid
from datetime import datetime, timedelta, timezone

import docx2txt
import requests
from bs4 import BeautifulSoup
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter


def get_current_beijing_time():
    SHA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    beijing_time = utc_now.astimezone(SHA_TZ).strftime("%Y-%m-%d-%H:%M:%S")
    return beijing_time


emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)


def clean_text(x):
    x = x.encode("ascii", "ignore").decode()  # unicode
    x = re.sub(r"https*\S+", " ", x)  # url
    x = re.sub(r"@\S+", " ", x)  # mentions
    x = re.sub(r"#\S+", " ", x)  # hastags
    x = re.sub(r"\s{2,}", " ", x)  # over spaces
    x = emoji_pattern.sub(r"", x)  # emojis
    x = re.sub("[^.,!?A-Za-z0-9]+", " ", x)  # special characters except .,!?

    return x


def fetch_article_text(url: str):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    results = soup.find_all(["h1", "p"])
    text = [result.text for result in results]
    ARTICLE = " ".join(text)
    ARTICLE = ARTICLE.replace(".", ".<eos>")
    ARTICLE = ARTICLE.replace("!", "!<eos>")
    ARTICLE = ARTICLE.replace("?", "?<eos>")
    sentences = ARTICLE.split("<eos>")
    current_chunk = 0
    chunks = []
    for sentence in sentences:
        if len(chunks) == current_chunk + 1:
            if len(chunks[current_chunk]) + len(sentence.split(" ")) <= 500:
                chunks[current_chunk].extend(sentence.split(" "))
            else:
                current_chunk += 1
                chunks.append(sentence.split(" "))
        else:
            print(current_chunk)
            chunks.append(sentence.split(" "))

    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = " ".join(chunks[chunk_id])

    return ARTICLE, chunks


def read_pdf(file):
    loader = PyPDFLoader(file)
    docs = loader.load_and_split()
    return docs


def read_text_from_file(file, save_file_name):
    # read text file
    if file.headers["content-type"] == "text/plain":
        file.file.seek(0)
        content = file.file.read().decode("utf-8")
        # Split text
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(content)
        # Create multiple documents
        file_content = [Document(page_content=t) for t in texts]
    # read pdf file
    elif file.headers["content-type"] == "application/pdf":
        file_content = read_pdf(save_file_name)

    # read docx file
    elif file.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        file_content = docx2txt.process(file)

    doc_id = f"doc_{str(uuid.uuid1())[:8]}"

    return doc_id, file_content
