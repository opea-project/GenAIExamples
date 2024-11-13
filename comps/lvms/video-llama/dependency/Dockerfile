# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.9-slim

ENV LANG=C.UTF-8

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    git git-lfs && \ 
    git lfs install

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user:user /home/user/
RUN mkdir /home/user/model && chown user:user -R /home/user/model

USER user

COPY --chown=user:user comps /home/user/comps
WORKDIR /home/user/comps/lvms/video-llama/dependency

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/lvms/video-llama/dependency/requirements.txt

ARG VIDEO_LLAMA_REPO=https://github.com/DAMO-NLP-SG/Video-LLaMA.git
ARG VIDEO_LLAMA_COMMIT=0adb19e
RUN tar -xvf video-llama.patch.tar && \
    git clone ${VIDEO_LLAMA_REPO} Video-LLaMA && \
    cd Video-LLaMA && git checkout ${VIDEO_LLAMA_COMMIT} && \
    git apply --whitespace=fix ../video-llama.patch && \
    mv video_llama ../ && \
    cd ../ && rm -rf Video-LLaMA


ENV PYTHONPATH=/home/user


ENTRYPOINT ["bash", "start.sh"]
