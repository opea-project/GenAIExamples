# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#FROM python:3.11-slim
FROM node:22.9.0

ENV LANG=C.UTF-8
ARG ARCH=cpu

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev \
    git \
    python3-venv


WORKDIR /root/

ENV HOME=/root
ENV VIRTUAL_ENV=$HOME/.env/open-webui

COPY open_webui_patches /root/patches

RUN git clone https://github.com/open-webui/open-webui.git && \
    git config --global user.name "opea" && git config --global user.email "" && \
    mkdir -p $HOME/.env && python3 -m venv $VIRTUAL_ENV && \
    $VIRTUAL_ENV/bin/python -m pip install --no-cache-dir --upgrade pip && \
    $VIRTUAL_ENV/bin/python -m pip install --no-cache-dir build

WORKDIR /root/open-webui

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN git checkout v0.5.20 && \
    git am ../patches/*.patch && \
    python -m build && \
    pip install --no-cache-dir dist/open_webui-0.5.20-py3-none-any.whl    

ENV LANG=en_US.UTF-8

WORKDIR /root/

RUN rm -fr /root/open-webui && rm -fr /root/patches

# CMD ["/bin/bash"]
ENTRYPOINT ["open-webui", "serve"]


