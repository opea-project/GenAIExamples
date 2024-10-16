# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

path = os.path.join(os.path.dirname(__file__), "./data/80000_docs")
for file in os.listdir(path):
    src_file = os.path.join(path, file)
    os.rename(src_file, src_file + ".txt")
