# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM $IMAGE_REPO/comps-base:$BASE_TAG

USER root

COPY ./requirements.txt $HOME/requirements.txt
COPY ./browser_use_agent.py $HOME/browser_use_agent.py

ARG uvpip='uv pip install --system --no-cache-dir'
RUN uv pip install --system --upgrade pip setuptools uv && \
    $uvpip pytest-playwright && \
    playwright install chromium --with-deps --no-shell && \
    $uvpip -r requirements.txt && \
    $uvpip posthog==5.4.0

USER user
ENTRYPOINT ["python", "browser_use_agent.py"]