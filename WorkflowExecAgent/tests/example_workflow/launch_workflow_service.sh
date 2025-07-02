#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

apt-get -qq -y install --no-install-recommends unzip curl ca-certificates
apt-get -qq -y install --no-install-recommends python3 python3-pip

curl -L -o ./archive.zip https://www.kaggle.com/api/v1/datasets/download/blastchar/telco-customer-churn
unzip ./archive.zip -d ./
rm ./archive.zip

pip install virtualenv && \
    virtualenv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt

uvicorn main:app --reload --port=5005 --host=0.0.0.0
