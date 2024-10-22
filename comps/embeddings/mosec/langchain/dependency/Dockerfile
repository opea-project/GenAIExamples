# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

ARG DEBIAN_FRONTEND=noninteractive

ENV GLIBC_TUNABLES glibc.cpu.x86_shstk=permissive

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip setuptools
RUN pip install --no-cache-dir torch==2.2.2 torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir intel-extension-for-pytorch==2.2.0
RUN pip install --no-cache-dir transformers llmspec mosec

RUN cd /home/user/ && export HF_ENDPOINT=https://hf-mirror.com && huggingface-cli download --resume-download BAAI/bge-large-zh-v1.5 --local-dir /home/user/bge-large-zh-v1.5
USER user
ENV MOSEC_EMBEDDING_MODEL="/home/user/bge-large-zh-v1.5/"

WORKDIR /home/user/comps/embeddings/mosec/langchain/dependency

CMD ["python3", "server-ipex.py"]
