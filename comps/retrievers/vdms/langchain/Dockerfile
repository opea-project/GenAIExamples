
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM langchain/langchain:latest

ARG ARCH="cpu"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    iputils-ping \
    vim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

COPY comps /home/user/comps

USER user
RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/user/comps/retrievers/vdms/langchain/requirements.txt

RUN pip install -U langchain
RUN pip install -U langchain-community

RUN pip install --upgrade huggingface-hub

ENV PYTHONPATH=$PYTHONPATH:/home/user

ENV HUGGINGFACEHUB_API_TOKEN=dummy

ENV USECLIP 0

ENV no_proxy=localhost,127.0.0.1

ENV http_proxy=""
ENV https_proxy=""

WORKDIR /home/user/comps/retrievers/vdms/langchain

ENTRYPOINT ["python", "retriever_vdms.py"]
