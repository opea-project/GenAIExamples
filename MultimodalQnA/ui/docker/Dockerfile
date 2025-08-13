# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    default-jre \
    libjemalloc-dev \
    ffmpeg \
    wget

RUN mkdir -p /home/user

COPY gradio /home/user/gradio

RUN pip install --no-cache-dir --upgrade pip setuptools && \
pip install --no-cache-dir -r /home/user/gradio/requirements.txt

WORKDIR /home/user/gradio
ENTRYPOINT ["python", "multimodalqna_ui_gradio.py"]
