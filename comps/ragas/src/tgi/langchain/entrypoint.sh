#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pip --no-cache-dir install -r requirements-runtime.txt

python llm.py
