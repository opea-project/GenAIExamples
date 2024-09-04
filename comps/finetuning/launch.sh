# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

if [[ -n "$RAY_PORT" ]];then
    ray start --head --port $RAY_PORT --dashboard-host=0.0.0.0
else
    ray start --head --dashboard-host=0.0.0.0
    export RAY_PORT=8265
fi

export RAY_ADDRESS=http://localhost:$RAY_PORT
python finetuning_service.py
