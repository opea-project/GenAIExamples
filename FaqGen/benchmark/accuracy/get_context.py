# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

import pandas as pd

data_path = "./data"
data = pd.read_parquet(os.path.join(data_path, "squad_v2/squad_v2/validation-00000-of-00001.parquet"))
sq_context = list(data["context"].unique())
sq_context_d = dict()
for i in range(len(sq_context)):
    sq_context_d[i] = sq_context[i]

with open(os.path.join(data_path, "sqv2_context.json"), "w") as outfile:
    json.dump(sq_context_d, outfile)
