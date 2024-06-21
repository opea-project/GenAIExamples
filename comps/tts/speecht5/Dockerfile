# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/home/user

# Install system dependencies
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get install -y curl

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/comps/tts/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/tts/speecht5

ENTRYPOINT ["python", "speecht5_server.py", "--device", "cpu"]