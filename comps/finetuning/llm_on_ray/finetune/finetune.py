# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 The LLM-on-Ray Authors.

#!/usr/bin/env python

import argparse
import os
import sys
from itertools import chain
from typing import Any, Dict, Optional

import datasets
import ray
import torch
import transformers
from peft import LoraConfig, get_peft_model
from pydantic_yaml import parse_yaml_raw_as
from ray.air import FailureConfig, RunConfig
from ray.air.config import ScalingConfig
from ray.train.torch import TorchTrainer
from transformers import Trainer, TrainingArguments

from comps import CustomLogger
from comps.finetuning.finetune_config import FinetuneConfig
from comps.finetuning.llm_on_ray import common
from comps.finetuning.llm_on_ray.finetune.data_process import (
    DPOCollator,
    DPODataProcessor,
    EmbedCollator,
    GroupCollator,
    InstructionDataProcessor,
    PretrainingDataProcessor,
    TrainDatasetForCE,
    TrainDatasetForEmbedding,
)
from comps.finetuning.llm_on_ray.finetune.modeling import BiEncoderModel, CrossEncoder

logger = CustomLogger("llm_on_ray/finetune")


def adapt_transformers_to_device(config: Dict):
    device = config["Training"]["device"]
    if device in ["hpu"]:
        from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

        # adapt transformers to gaudi
        adapt_transformers_to_gaudi()


def set_seed(config: Dict):
    seed = config["Training"].get("seed", None)
    if seed is None:
        return
    device = config["Training"]["device"]
    if device in ["cpu", "gpu"]:
        from accelerate.utils import set_seed as _set_seed

        _set_seed(seed)
    elif device in ["hpu"]:
        from optimum.habana.utils import set_seed as _set_seed

        _set_seed(seed)


def convert_to_training_args(cls, config: Dict):
    device = config["Training"]["device"]
    accelerate_mode = config["Training"]["accelerate_mode"]
    save_strategy = config["General"]["save_strategy"]

    args = {
        "output_dir": config["General"]["output_dir"],
        "report_to": config["General"]["report_to"],
        "resume_from_checkpoint": config["General"]["resume_from_checkpoint"],
        "gradient_checkpointing": config["General"]["enable_gradient_checkpointing"],
        "save_strategy": save_strategy if save_strategy != "False" else "no",
        "bf16": config["Training"]["mixed_precision"] == "bf16",
        "num_train_epochs": config["Training"]["epochs"],
        "per_device_train_batch_size": config["Training"]["batch_size"],
        "per_device_eval_batch_size": config["Training"]["batch_size"],
        "optim": config["Training"]["optimizer"],
        "learning_rate": config["Training"]["learning_rate"],
        "logging_steps": config["Training"]["logging_steps"],
        "lr_scheduler_type": config["Training"]["lr_scheduler"],
        "weight_decay": config["Training"]["weight_decay"],
        "gradient_accumulation_steps": config["Training"]["gradient_accumulation_steps"],
        "do_train": True,
    }

    # set attr do_eval
    vf = config["Dataset"].get("validation_file", None)
    vsp = config["Dataset"].get("validation_split_percentage", 0)
    if vf is not None or (vsp / 100 > 0.0 and vsp / 100 < 1.0):
        args.update({"do_eval": True})

    # set attr max_steps
    if config["Training"]["max_train_steps"] is not None:
        args.update({"max_steps": config["Training"]["max_train_steps"]})

    # set attr for device cpu
    if device == "cpu":
        if hasattr(cls, "use_cpu"):
            args.update({"use_cpu": True})
        if hasattr(cls, "no_cuda"):
            args.update({"no_cuda": True})
        args.update({"use_ipex": True})

    # set attr 'deepspeed'
    if accelerate_mode == "DEEPSPEED":
        args.update({"deepspeed": config["Training"]["deepspeed_config_file"]})

    # set attr for FSDP
    # if accelerate_mode == "FSDP":
    #     args.updatwe({})

    # set attr for Intel Gaudi
    if device == "hpu":
        args.update({"use_habana": True})
        args.update({"use_lazy_mode": config["Training"]["hpu_execution_mode"] == "lazy"})
        args.update({"pipelining_fwd_bwd": True})

    return cls(**args)


def convert_dtype(dtype: str) -> Optional[torch.dtype]:
    supported_dtypes = {
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
        "no": None,
    }
    return supported_dtypes[dtype]


def load_tokenizer(config: Dict):
    if config["General"].get("tokenizer_name") is not None:
        tokenizer_name = config["General"].get("tokenizer_name")
    else:
        tokenizer_name = config["General"]["base_model"]
    load_config = config["General"].get("config", {})
    # default padding side is right
    padding_side = config["Dataset"].get("padding_side", "right")
    # default truncation side is right
    truncation_side = config["Dataset"].get("truncation_side", "right")
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        tokenizer_name, padding_side=padding_side, truncation_side=truncation_side, **load_config
    )
    return tokenizer


def load_dataset(config: Dict):
    dataset_file = config["Dataset"].get("train_file", None)
    if dataset_file is None:
        return

    if os.path.exists(dataset_file):
        # load from local file
        def local_load(name, **load_config):
            if os.path.isfile(name):
                file = os.path.basename(os.path.abspath(name))
                path = os.path.dirname(os.path.abspath(name))
                dataset = datasets.load_dataset(path, data_files=file, **load_config)
            else:
                dataset = datasets.load_dataset(name, **load_config)
            return dataset["train"]

        train_dataset = local_load(dataset_file)
        validation_file = config["Dataset"].get("validation_file", None)
        if validation_file is not None:
            validation_dataset = local_load(validation_file)
            return datasets.DatasetDict({"train": train_dataset, "validation": validation_dataset})

        validation_split_percentage = config["Dataset"].get("validation_split_percentage", 0)
        if validation_split_percentage / 100 > 0.0 and validation_split_percentage / 100 < 1.0:
            dataset_dict = train_dataset.train_test_split(test_size=validation_split_percentage / 100)
            dataset_dict["validation"] = dataset_dict["test"]
            return dataset_dict

        return datasets.DatasetDict({"train": train_dataset})
    else:
        # try to download and load dataset from huggingface.co
        load_config = config["General"].get("config", {})
        use_auth_token = load_config.get("token", None)
        raw_dataset = datasets.load_dataset(dataset_file, token=use_auth_token)

        validation_split_percentage = config["Dataset"].get("validation_split_percentage", 0)
        if "validation" not in raw_dataset.keys() and (
            validation_split_percentage / 100 > 0.0 and validation_split_percentage / 100 < 1.0
        ):
            dataset_dict = raw_dataset["train"].train_test_split(test_size=validation_split_percentage / 100)
            dataset_dict["validation"] = dataset_dict["test"]
            return dataset_dict

        return raw_dataset


def tokenize_dataset(config: Dict, tokenizer, dataset):
    task = config["General"].get("task", "instruction_tuning")
    if task == "instruction_tuning":
        group = config["Dataset"].get("group", True)
        block_size = config["Dataset"].get("block_size", 512)
        tokenizer.pad_token = tokenizer.eos_token if not tokenizer.pad_token else tokenizer.pad_token

        processor = InstructionDataProcessor(config, tokenizer)

        for key in dataset:
            prompts = processor.make_prompt(dataset[key])
            dataset[key] = datasets.Dataset.from_dict(prompts)

        column_names = list(dataset["train"].features)
        tokenize_fn = (
            processor.tokenize_by_neural_chat
            if config["Dataset"].get("data_preprocess_type", "") == "neural_chat"
            else processor.tokenize
        )

        tokenized_dataset = dataset.map(
            tokenize_fn,
            remove_columns=column_names,
            batched=True,
            load_from_cache_file=False,
            desc="Tokenize dataset",
        )

        if group:

            def group_texts(examples):
                # Concatenate all texts.
                concatenated_examples = {k: list(chain(*examples[k])) for k in examples.keys()}
                total_length = len(concatenated_examples[list(examples.keys())[0]])
                # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
                # customize this part to your needs.
                if total_length >= block_size:
                    total_length = (total_length // block_size) * block_size
                # Split by chunks of max_len.
                result = {
                    k: [t[i : i + block_size] for i in range(0, total_length, block_size)]
                    for k, t in concatenated_examples.items()
                }
                return result

            tokenized_dataset = tokenized_dataset.map(
                group_texts,
                batched=True,
                load_from_cache_file=False,
                desc=f"Grouping texts in chunks of {block_size}",
            )

        return tokenized_dataset
    elif task == "pretraining":
        group = True
        block_size = config["Dataset"].get("block_size", 512)
        tokenizer.pad_token = tokenizer.eos_token if not tokenizer.pad_token else tokenizer.pad_token

        processor = PretrainingDataProcessor(config, tokenizer)

        column_names = list(dataset["train"].features)

        tokenized_dataset = dataset.map(
            processor.tokenize,
            remove_columns=column_names,
            batched=True,
            load_from_cache_file=False,
            desc="Tokenize dataset",
        )

        if group:

            def group_texts(examples):
                # Concatenate all texts.
                concatenated_examples = {k: list(chain(*examples[k])) for k in examples.keys()}
                total_length = len(concatenated_examples[list(examples.keys())[0]])
                # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
                # customize this part to your needs.
                if total_length >= block_size:
                    total_length = (total_length // block_size) * block_size
                # Split by chunks of max_len.
                result = {
                    k: [t[i : i + block_size] for i in range(0, total_length, block_size)]
                    for k, t in concatenated_examples.items()
                }
                return result

            tokenized_dataset = tokenized_dataset.map(
                group_texts,
                batched=True,
                load_from_cache_file=False,
                desc=f"Grouping texts in chunks of {block_size}",
            )

        return tokenized_dataset
    elif task == "dpo":
        tokenizer.pad_token = tokenizer.eos_token if not tokenizer.pad_token else tokenizer.pad_token
        processor = DPODataProcessor(config, tokenizer)
        column_names = dataset["train"].column_names
        tokenized_dataset = dataset.map(
            processor.tokenize,
            remove_columns=column_names,
            batched=True,
            load_from_cache_file=False,
            desc="Tokenize dataset",
        )
        return tokenized_dataset
    elif task == "rerank":
        dataset["train"] = TrainDatasetForCE(dataset["train"], config["Dataset"], tokenizer)
        return dataset
    elif task == "embedding":
        dataset["train"] = TrainDatasetForEmbedding(dataset["train"], config["Dataset"], tokenizer)
        return dataset
    else:
        raise NotImplementedError(f"Unsupported task {task}, only support instruction_tuning, rerank, embedding now.")


def prepare_data_collator(config: Dict, tokenizer):
    task = config["General"].get("task", "instruction_tuning")
    if task == "instruction_tuning" or task == "pretraining":
        return transformers.DataCollatorForLanguageModeling(
            tokenizer=tokenizer, mlm=False, return_tensors="pt", pad_to_multiple_of=8
        )
    elif task == "dpo":
        return DPOCollator(tokenizer)
    elif task == "rerank":
        return GroupCollator(tokenizer)
    elif task == "embedding":
        return EmbedCollator(
            tokenizer=tokenizer,
            padding=config["Dataset"]["padding"],
            query_max_len=config["Dataset"]["query_max_len"],
            passage_max_len=config["Dataset"]["passage_max_len"],
        )
    else:
        raise NotImplementedError(f"Unsupported task {task}, only support instruction_tuning, rerank, embedding now.")


def load_model(config: Dict):
    model_name = config["General"]["base_model"]
    model_dtype = convert_dtype(config["Training"].get("mixed_precision", "no"))
    model_config = config["General"].get("config", {})
    task = config["General"].get("task", "instruction_tuning")
    ref_model = None
    if task in ["instruction_tuning", "pretraining", "dpo"]:
        model = transformers.AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=model_dtype, **model_config)
        if task == "dpo":
            ref_model = transformers.AutoModelForCausalLM.from_pretrained(
                model_name, torch_dtype=model_dtype, **model_config
            )
        lora_config = config["General"].get("lora_config", None)
        if lora_config and task == "instruction_tuning":
            peft_config = LoraConfig(**lora_config)
            model = get_peft_model(model, peft_config)
    elif task == "rerank":
        model = CrossEncoder.from_pretrained(
            config["Dataset"].get("train_group_size", 8),
            config["Training"]["batch_size"],
            model_name,
            from_tf=bool(".ckpt" in model_name),
            config=model_config,
        )
    elif task == "embedding":
        should_concat = False
        if (
            config["Dataset"]["query_max_len"] == config["Dataset"]["passage_max_len"]
            and config["Dataset"]["padding"] == "max_length"
        ):
            should_concat = True
        if config["Training"]["device"] == "hpu" and not should_concat:
            raise ValueError("please set query_max_len==passage_max_len and padding='max_length' for hpu.")

        if config["Training"].get("embedding_training_config", None) is not None:
            model = BiEncoderModel(
                model_name=model_name, should_concat=should_concat, **config["Training"]["embedding_training_config"]
            )
        else:
            model = BiEncoderModel(model_name=model_name, should_concat=should_concat)
    else:
        raise NotImplementedError(f"Unsupported task {task}, only support instruction_tuning, rerank, embedding now.")

    egc = config["General"].get("enable_gradient_checkpointing", False)
    if egc:
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    model.to(dtype=model_dtype, device=torch.device(config["Training"]["device"]))

    return model, ref_model


def get_trainer(config: Dict, model, ref_model, tokenizer, tokenized_dataset, data_collator):
    device = config["Training"]["device"]
    task = config["General"].get("task", "instruction_tuning")
    if device in ["cpu", "gpu", "cuda"]:
        training_args = convert_to_training_args(TrainingArguments, config)
        if task == "dpo":
            lora_config = config["General"].get("lora_config", None)
            peft_config = LoraConfig(**lora_config)
            from comps.finetuning.llm_on_ray.finetune.dpo_trainer import DPOTrainer

            trainer = DPOTrainer(
                model,
                ref_model,
                args=training_args,
                data_collator=data_collator,
                beta=config["Training"].get("dpo_beta", 0.1),
                train_dataset=tokenized_dataset["train"],
                eval_dataset=(
                    tokenized_dataset["validation"] if tokenized_dataset.get("validation") is not None else None
                ),
                tokenizer=tokenizer,
                peft_config=peft_config,
                max_length=config["Dataset"].get("max_length", 1024),
            )
        else:
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset["train"],
                eval_dataset=(
                    tokenized_dataset["validation"] if tokenized_dataset.get("validation") is not None else None
                ),
                tokenizer=tokenizer,
                data_collator=data_collator,
            )
        return training_args, trainer
    elif device in ["hpu"]:
        from optimum.habana import GaudiConfig
        from optimum.habana.transformers import GaudiTrainer, GaudiTrainingArguments

        training_args = convert_to_training_args(GaudiTrainingArguments, config)

        if task == "dpo":
            lora_config = config["General"].get("lora_config", None)
            peft_config = LoraConfig(**lora_config)
            from comps.finetuning.llm_on_ray.finetune.dpo_trainer import GaudiDPOTrainer

            trainer = GaudiDPOTrainer(
                model,
                ref_model,
                args=training_args,
                data_collator=data_collator,
                beta=config["Training"].get("dpo_beta", 0.1),
                train_dataset=tokenized_dataset["train"],
                eval_dataset=(
                    tokenized_dataset["validation"] if tokenized_dataset.get("validation") is not None else None
                ),
                tokenizer=tokenizer,
                peft_config=peft_config,
                max_length=config["Dataset"].get("max_length", 1024),
            )
        else:
            # If gaudi_config_name is provided, load gaudi_config from huggingface model hub(https://huggingface.co/Habana), otherwise use default gaudi_config
            gaudi_config_name = config["General"].get("gaudi_config_name", None)
            if gaudi_config_name is not None:
                gaudi_config = GaudiConfig.from_pretrained(gaudi_config_name)
            else:
                gaudi_config = GaudiConfig()
                gaudi_config.use_fused_adam = True
                gaudi_config.use_fused_clip_norm = True

            trainer = GaudiTrainer(
                model=model,
                args=training_args,
                gaudi_config=gaudi_config,
                train_dataset=tokenized_dataset["train"],
                eval_dataset=(
                    tokenized_dataset["validation"] if tokenized_dataset.get("validation") is not None else None
                ),
                tokenizer=tokenizer,
                data_collator=data_collator,
            )
        return training_args, trainer
    return None, None


def train_func(config: Dict[str, Any]):
    os.chdir(config["cwd"])

    adapt_transformers_to_device(config)

    set_seed(config)

    tokenizer = load_tokenizer(config)

    dataset = load_dataset(config)

    max_train_samples = config["Dataset"].get("max_train_samples", 0)
    if 0 < max_train_samples < len(dataset["train"]):
        dataset["train"] = dataset["train"].select(range(max_train_samples))

    max_eval_samples = config["Dataset"].get("max_eval_samples", 0)
    if "validation" in dataset and 0 < max_eval_samples < len(dataset["validation"]):
        dataset["validation"] = dataset["validation"].select(range(max_eval_samples))

    tokenized_dataset = tokenize_dataset(config, tokenizer, dataset)

    data_collator = prepare_data_collator(config, tokenizer)

    model, ref_model = load_model(config)

    training_args, trainer = get_trainer(config, model, ref_model, tokenizer, tokenized_dataset, data_collator)

    logger.info("train start")
    trainer.train(resume_from_checkpoint=training_args.resume_from_checkpoint)
    trainer.save_model()
    logger.info("train finish")


def get_finetune_config():
    parser = argparse.ArgumentParser(description="Finetune a transformers model on a causal language modeling task")
    parser.add_argument(
        "--config_file",
        type=str,
        required=True,
        default=None,
        help="The name of the dataset to use (via the datasets library).",
    )

    # Print help if no arguments were provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    config_file = args.config_file

    with open(config_file) as f:
        finetune_config = parse_yaml_raw_as(FinetuneConfig, f)
    return finetune_config.dict()


def main(external_config=None):
    if not external_config:
        config = get_finetune_config()
    else:
        config = external_config

    config["cwd"] = os.getcwd()

    num_training_workers = config["Training"].get("num_training_workers")
    resources_per_worker = config["Training"].get("resources_per_worker")

    if num_training_workers > 1 and config["Training"].get("accelerate_mode", None) is None:
        config["Training"]["accelerate_mode"] = "DDP"  # will use DDP to accelerate if no method specified

    ccl_worker_count = 1
    device = config["Training"]["device"]
    if device != "cpu":
        ccl_worker_count = num_training_workers

    if not ray.is_initialized():
        runtime_env = {
            "env_vars": {
                "OMP_NUM_THREADS": str(resources_per_worker["CPU"]),
                "CCL_ZE_IPC_EXCHANGE": "sockets",
                "CCL_WORKER_COUNT": str(ccl_worker_count),
                "CCL_LOG_LEVEL": "info",
                "FI_TCP_IFACE": "lo",
                "FI_PROVIDER": "tcp",
            }
        }

        if config["General"]["gpt_base_model"] is True:
            runtime_env["pip"] = ["transformers==4.26.0"]

        if device == "gpu":
            num_cpus = resources_per_worker["CPU"] * num_training_workers + 1  # additional 1 for head worker
            ray.init(num_cpus=num_cpus, runtime_env=runtime_env)
        else:
            ray.init(runtime_env=runtime_env)

    logger.info(f"ray available resources = {ray.available_resources()}")

    use_gpu = True if device == "gpu" else False
    scaling_config = ScalingConfig(
        num_workers=num_training_workers,
        use_gpu=use_gpu,
        resources_per_worker=resources_per_worker,
        placement_strategy="SPREAD",
    )

    # if try to use Intel GPU, convert device to 'xpu'
    # due to accelerate internal use 'xpu' represent Intel GPU
    if device == "gpu":
        from accelerate.utils import is_xpu_available

        if is_xpu_available():
            device = "xpu"

    if config.get("torch_config", None) is None:
        backend = None
        if device == "cpu" or device == "xpu" or device == "gpu":
            backend = "ccl"
        elif device == "hpu":
            backend = "hccl"
        torch_config = common.TorchConfig(backend=backend, device=device)
    else:
        customer_torch_config = config.get("torch_config")
        torch_config = common.TorchConfig(**customer_torch_config, device=device)

    if config.get("failure_config", None) is None:
        failure_config = FailureConfig()
    else:
        customer_failure_config = config.get("failure_config")
        failure_config = FailureConfig(**customer_failure_config)

    if config.get("run_config", None) is None:
        run_config = RunConfig(failure_config=failure_config)
    else:
        customer_run_config = config.get("run_config")
        if customer_run_config.get("failure_config", None) is None:
            customer_run_config["failure_config"] = failure_config
        run_config = RunConfig(**customer_run_config)

    trainer = TorchTrainer(
        train_func,
        train_loop_config=config,
        scaling_config=scaling_config,
        torch_config=torch_config,
        run_config=run_config,
    )
    results = trainer.fit()
    if external_config is not None:
        return results


if __name__ == "__main__":
    main()
