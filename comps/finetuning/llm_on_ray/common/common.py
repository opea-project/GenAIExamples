# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 The LLM-on-Ray Authors.

import glob
import importlib
import os

from .logging import logger


def import_all_modules(basedir, prefix=None):
    all_py_files = glob.glob(basedir + "/*.py")
    modules = [os.path.basename(f) for f in all_py_files]

    for module in modules:
        if not module.startswith("_"):
            module = module.rstrip(".py")
            if prefix is None:
                module_name = module
            else:
                module_name = f"{prefix}.{module}"
            try:
                importlib.import_module(module_name)
            except Exception:
                logger.warning(f"import {module_name} error", exc_info=True)
