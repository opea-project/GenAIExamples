# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM $IMAGE_REPO/comps-base:$BASE_TAG

USER root
# FFmpeg needed for media processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
USER user

COPY ./arb_post_hearing_assistant.py $HOME/arb_post_hearing_assistant.py

ENTRYPOINT ["python", "arb_post_hearing_assistant.py"]
