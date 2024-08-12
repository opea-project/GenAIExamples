# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim


RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

# Set environment variables
ENV LANG=en_US.UTF-8

# Install system dependencies
RUN apt-get update \
    && apt-get install -y ffmpeg

COPY --chown=user:user comps /home/user/comps

USER user

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/asr/requirements.txt && \
    pip list

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/asr/whisper

ENTRYPOINT ["python", "whisper_server.py", "--device", "cpu"]