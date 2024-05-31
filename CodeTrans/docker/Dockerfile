

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim \
    git

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

RUN cd /home/user/ && \
    git clone https://github.com/opea-project/GenAIComps.git

RUN cd /home/user/GenAIComps && pip install --no-cache-dir --upgrade pip && \
    pip install -r /home/user/GenAIComps/requirements.txt

COPY ./code_translation.py /home/user/code_translation.py

ENV PYTHONPATH=$PYTHONPATH:/home/user/GenAIComps

USER user

WORKDIR /home/user

ENTRYPOINT ["python", "code_translation.py"]
