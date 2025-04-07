# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8
ARG ARCH=cpu

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev \
    git


WORKDIR /root/

COPY open_webui_patches /root/patches

RUN git clone https://github.com/open-webui/open-webui.git && \
    git config --global user.name "opea" && git config --global user.email "" && \
    cd open-webui && git checkout v0.5.20 && \
    git am ../patches/*.patch && \
    pip install --no-cache-dir open-webui==0.5.20 && \
    cp /root/open-webui/backend/open_webui/utils/middleware.py /usr/local/lib/python3.11/site-packages/open_webui/utils/middleware.py

ENV LANG=en_US.UTF-8

WORKDIR /root/

# CMD ["/bin/bash"]
ENTRYPOINT ["open-webui", "serve"]


