# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM $IMAGE_REPO/comps-base:$BASE_TAG

RUN apt update && apt install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt install python3.12 python3.12-venv python3.12-distutils -y python3.12 --version && \
    playwright install chromium --with-deps --no-shell && \
    apt clean && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt $HOME/requirements.txt
COPY ./browser_use_agent.py $HOME/browser_use_agent.py

USER root
ARG uvpip='uv pip install --system --no-cache-dir'
RUN pip install --no-cache-dir --upgrade pip setuptools uv && \
    $uvpip -r requirements.txt && \
    chown -R user:user $HOME

USER user

ENTRYPOINT ["python", "browser_use_agent.py"]
