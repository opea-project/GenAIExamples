# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG

COPY ./videoqna.py $HOME/videoqna.py

ENTRYPOINT ["python", "videoqna.py"]
