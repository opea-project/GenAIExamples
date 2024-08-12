# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

From ubuntu:22.04
RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/
ARG DEBIAN_FRONTEND=noninteractive

ENV GLIBC_TUNABLES glibc.cpu.x86_shstk=permissive
RUN apt update && apt install -y python3 python3-pip 

USER user
COPY comps /home/user/comps

RUN pip3 install torch==2.2.2 torchvision --index-url https://download.pytorch.org/whl/cpu 
RUN pip3 install intel-extension-for-pytorch==2.2.0
RUN pip3 install transformers
RUN pip3 install llmspec mosec

RUN cd /home/user/ && export HF_ENDPOINT=https://hf-mirror.com && huggingface-cli download --resume-download BAAI/bge-large-zh-v1.5 --local-dir /home/user/bge-large-zh-v1.5

ENV EMB_MODEL="/home/user/bge-large-zh-v1.5/"

WORKDIR /home/user/comps/embeddings/langchain-mosec/mosec-docker

CMD ["python3", "server-ipex.py"]
