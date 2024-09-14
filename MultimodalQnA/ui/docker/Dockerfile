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
WORKDIR /root
RUN wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz && \
    mkdir ffmpeg-git-amd64-static && tar -xvf ffmpeg-git-amd64-static.tar.xz -C ffmpeg-git-amd64-static --strip-components 1 && \
    export PATH=/root/ffmpeg-git-amd64-static:$PATH && \
    cp /root/ffmpeg-git-amd64-static/ffmpeg /usr/local/bin/ && \
    cp /root/ffmpeg-git-amd64-static/ffprobe /usr/local/bin/

RUN mkdir -p /home/user

COPY gradio /home/user/gradio

RUN pip install --no-cache-dir --upgrade pip setuptools && \
pip install --no-cache-dir -r /home/user/gradio/requirements.txt

WORKDIR /home/user/gradio
ENTRYPOINT ["python", "multimodalqna_ui_gradio.py"]
# ENTRYPOINT ["/usr/bin/sleep", "infinity"]