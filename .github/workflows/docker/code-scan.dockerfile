# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG UBUNTU_VER=22.04
FROM ubuntu:${UBUNTU_VER} as devel

ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    aspell \
    aspell-en \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    python3-distutils \
    wget

RUN ln -sf $(which python3) /usr/bin/python

RUN python -m pip install --no-cache-dir bandit==1.7.8
RUN wget -O /bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
RUN chmod +x /bin/hadolint

WORKDIR /
