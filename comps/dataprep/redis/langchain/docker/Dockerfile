# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    default-jre \
    libgl1-mesa-glx \
    libjemalloc-dev \
    libreoffice \
    poppler-utils \
    tesseract-ocr

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    if [ ${ARCH} = "cpu" ]; then pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/user/comps/dataprep/redis/langchain/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

USER root

RUN mkdir -p /home/user/comps/dataprep/redis/langchain/uploaded_files && chown -R user /home/user/comps/dataprep/redis/langchain/uploaded_files

USER user

WORKDIR /home/user/comps/dataprep/redis/langchain

ENTRYPOINT ["python", "prepare_doc_redis.py"]
