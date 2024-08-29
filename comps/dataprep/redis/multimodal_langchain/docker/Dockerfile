# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev \
    default-jre \
    wget \
    vim

# Install ffmpeg static build
RUN cd /root && wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz && \
    mkdir ffmpeg-git-amd64-static && tar -xvf ffmpeg-git-amd64-static.tar.xz -C ffmpeg-git-amd64-static --strip-components 1 && \
    export PATH=/root/ffmpeg-git-amd64-static:$PATH && \
    cp /root/ffmpeg-git-amd64-static/ffmpeg /usr/local/bin/

RUN mkdir -p /home/user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    if [ ${ARCH} = "cpu" ]; then pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/user/comps/dataprep/redis/multimodal_langchain/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/dataprep/redis/multimodal_langchain

ENTRYPOINT ["python", "prepare_videodoc_redis.py"]

