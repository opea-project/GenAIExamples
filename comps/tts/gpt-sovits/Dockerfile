# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.10-slim
RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg git-lfs git wget vim build-essential numactl && \
    apt-get install -y libomp-dev google-perftools && \
    pip install --upgrade pip

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libiomp5.so:/usr/lib/x86_64-linux-gnu/libtcmalloc.so.4
ENV MALLOC_CONF="oversize_threshold:1,background_thread:true,metadata_thp:auto,dirty_decay_ms:9000000000,muzzy_decay_ms:9000000000"

# Clone source repo
RUN git clone --branch openai_compat --single-branch https://github.com/Spycsh/GPT-SoVITS.git
# Download pre-trained models, and prepare env
RUN git clone https://huggingface.co/lj1995/GPT-SoVITS pretrained_models
RUN mv pretrained_models/*  GPT-SoVITS/GPT_SoVITS/pretrained_models/ && \
    rm -rf pretrained_models && \
    pip install --no-cache-dir -r GPT-SoVITS/requirements.txt && \
    python -m nltk.downloader averaged_perceptron_tagger_eng cmudict

RUN mv GPT-SoVITS /home/user/
RUN mv /root/nltk_data /home/user/
RUN chown -R user /home/user/

USER user
# ENV LANG=C.UTF-8

WORKDIR /home/user/GPT-SoVITS

RUN wget "https://github.com/intel/intel-extension-for-transformers/raw/refs/heads/main/intel_extension_for_transformers/neural_chat/assets/audio/welcome_cn.wav"

ENTRYPOINT ["python", "api.py", "--default_refer_path", "./welcome_cn.wav", "--default_refer_text", "欢迎使用", "--default_refer_language", "zh"]
