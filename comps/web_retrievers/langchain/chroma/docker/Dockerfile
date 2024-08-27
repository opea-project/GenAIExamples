# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM langchain/langchain:latest

ARG ARCH="cpu"  # Set this to "cpu" or "gpu"

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then \
      pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /home/user/comps/web_retrievers/langchain/chroma/requirements.txt; \
    else \
      pip install --no-cache-dir -r /home/user/comps/web_retrievers/langchain/chroma/requirements.txt; \
    fi

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/web_retrievers/langchain/chroma

ENTRYPOINT ["python", "retriever_chroma.py"]
