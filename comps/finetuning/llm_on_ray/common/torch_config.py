# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 The LLM-on-Ray Authors.

import os
import sys
from dataclasses import dataclass
from typing import Optional

from ray.train._internal.worker_group import WorkerGroup
from ray.train.torch.config import TorchConfig as RayTorchConfig
from ray.train.torch.config import _TorchBackend

# The package importlib_metadata is in a different place, depending on the Python version.
if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata


@dataclass
class TorchConfig(RayTorchConfig):
    device: Optional[str] = None

    @property
    def backend_cls(self):
        EnableCCLBackend.device = self.device
        return EnableCCLBackend


def xpu_libs_import():
    """Try to import IPEX and oneCCL."""
    try:
        import intel_extension_for_pytorch
    except ImportError:
        raise ImportError("Please install intel_extension_for_pytorch")
    try:
        ccl_version = importlib_metadata.version("oneccl_bind_pt")
        if ccl_version >= "1.12":
            import oneccl_bindings_for_pytorch
        else:
            import torch_ccl
    except ImportError as ccl_not_exist:
        raise ImportError("Please install torch-ccl") from ccl_not_exist


def hpu_libs_import():
    """Try to import habana frameworkfs for torch."""
    try:
        import habana_frameworks.torch  # noqa: F401
    except ImportError as habana_not_exist:
        raise ImportError("Please install habana_frameworks") from habana_not_exist


def _set_torch_distributed_env_vars(device):
    if device is not None:
        os.environ["ACCELERATE_TORCH_DEVICE"] = device


class EnableCCLBackend(_TorchBackend):
    device: Optional[str] = None

    def on_start(self, worker_group: WorkerGroup, backend_config: RayTorchConfig):
        libs_import = hpu_libs_import if self.device is not None and self.device.startswith("hpu") else xpu_libs_import
        for i in range(len(worker_group)):
            worker_group.execute_single_async(i, libs_import)
        super().on_start(worker_group, backend_config)

    def on_training_start(self, worker_group: WorkerGroup, backend_config: RayTorchConfig):
        super().on_training_start(worker_group, backend_config)
        worker_group.execute(_set_torch_distributed_env_vars, self.device)
