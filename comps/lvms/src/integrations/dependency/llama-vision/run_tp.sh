#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

python gaudi_spawn.py --use_deepspeed --world_size 4 lvm_tp_serve.py &
python lvm_tp.py
