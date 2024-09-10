# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim
RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/home/user
ARG ARCH=cpu

# Install system dependencies
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get install -y curl

COPY --chown=user:user comps /home/user/comps

USER user

RUN pip install --no-cache-dir --upgrade pip && \
    if [ "${ARCH}" = "cpu" ]; then \
        pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu ; \
        pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /home/user/comps/tts/speecht5/requirements.txt ; \
    else \
        pip install --no-cache-dir -r /home/user/comps/tts/speecht5/requirements.txt ; \
    fi

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/tts/speecht5/dependency

ENTRYPOINT ["python", "speecht5_server.py", "--device", "cpu"]
