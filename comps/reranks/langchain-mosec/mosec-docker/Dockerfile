# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

From ubuntu:22.04
RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/
ARG DEBIAN_FRONTEND=noninteractive

ENV GLIBC_TUNABLES glibc.cpu.x86_shstk=permissive

COPY comps /home/user/comps

RUN apt update && apt install -y python3 python3-pip 

RUN pip3 install torch==2.2.2 torchvision --trusted-host download.pytorch.org --index-url https://download.pytorch.org/whl/cpu 
RUN pip3 install intel-extension-for-pytorch==2.2.0
RUN pip3 install transformers sentence-transformers
RUN pip3 install llmspec mosec

RUN cd /home/user/ && export HF_ENDPOINT=https://hf-mirror.com && huggingface-cli download --resume-download BAAI/bge-reranker-large --local-dir /home/user/bge-reranker-large
USER user
ENV EMB_MODEL="/home/user/bge-reranker-large/"

WORKDIR /home/user/comps/reranks/langchain-mosec/mosec-docker

CMD ["python3", "server-ipex.py"]
