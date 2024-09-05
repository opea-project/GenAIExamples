

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim


RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    git

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

WORKDIR /home/user/
RUN git clone https://github.com/opea-project/GenAIComps.git

WORKDIR /home/user/GenAIComps
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/GenAIComps/requirements.txt

COPY ./faqgen.py /home/user/faqgen.py

ENV PYTHONPATH=$PYTHONPATH:/home/user/GenAIComps

USER user

WORKDIR /home/user

ENTRYPOINT ["python", "faqgen.py"]
