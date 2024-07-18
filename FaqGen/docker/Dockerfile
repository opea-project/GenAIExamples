

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM langchain/langchain:latest

COPY GenAIComps /home/user/GenAIComps

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

RUN cd /home/user/GenAIComps && pip install --no-cache-dir --upgrade pip && \
    pip install -r /home/user/GenAIComps/requirements.txt

COPY GenAIExamples/FaqGen/docker/faqgen.py /home/user/faqgen.py

ENV PYTHONPATH=$PYTHONPATH:/home/user/GenAIComps

USER user

WORKDIR /home/user

ENTRYPOINT ["python", "faqgen.py"]
