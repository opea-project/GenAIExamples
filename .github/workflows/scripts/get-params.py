#!/usr/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../one_click_deploy/core/"))
from config import EXAMPLE_CONFIGS


def get_example_defaults(example_name):
    if example_name not in EXAMPLE_CONFIGS:
        print(f"error: example '{example_name}' not found in EXAMPLE_CONFIGS")
        sys.exit(1)

    example_config = EXAMPLE_CONFIGS[example_name]
    params = example_config.get("interactive_params", {})

    if isinstance(params, list):
        return {param["name"]: param["default"] for param in params}
    elif isinstance(params, dict):
        return {
            device: {param["name"]: param["default"] for param in device_params}
            for device, device_params in params.items()
        }
    else:
        return {"error": "Invalid params format in EXAMPLE_CONFIGS for example: " + example_name}


def main():
    example_name = sys.argv[1]

    defaults = get_example_defaults(example_name)

    print(json.dumps(defaults, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
