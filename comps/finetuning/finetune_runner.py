# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse

from pydantic_yaml import parse_yaml_raw_as
from transformers import TrainerCallback, TrainerControl, TrainerState, TrainingArguments

from comps.finetuning.llm_on_ray.finetune.finetune_config import FinetuneConfig


class FineTuneCallback(TrainerCallback):
    def __init__(self) -> None:
        super().__init__()

    def on_log(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
        print("FineTuneCallback:", args, state)


def main():
    parser = argparse.ArgumentParser(description="Runner for llm_on_ray-finetune")
    parser.add_argument("--config_file", type=str, required=True, default=None)
    args = parser.parse_args()
    model_config_file = args.config_file

    with open(model_config_file) as f:
        finetune_config = parse_yaml_raw_as(FinetuneConfig, f).model_dump()

    callback = FineTuneCallback()
    finetune_config["Training"]["callbacks"] = [callback]

    from comps.finetuning.llm_on_ray.finetune.finetune import main as llm_on_ray_finetune_main

    llm_on_ray_finetune_main(finetune_config)


if __name__ == "__main__":
    main()
