# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG

COPY ./translation.py $HOME/translation.py

ENTRYPOINT ["python", "translation.py"]
