# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM $IMAGE_REPO/comps-base:$BASE_TAG
COPY ./audioqna.py 1.py
COPY ./audioqna.py 2.py
COPY ./audioqna.py 3.py

COPY ./audioqna.py $HOME/audioqna.py

ENTRYPOINT ["python", "audioqna.py"]
