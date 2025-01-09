# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 The LLM-on-Ray Authors.

from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from comps.cores.proto.api_protocol import FineTuningJobsRequest

PRECISION_BF16 = "bf16"
PRECISION_FP16 = "fp16"
PRECISION_NO = "no"

DEVICE_CPU = "cpu"
DEVICE_HPU = "hpu"
DEVICE_GPU = "gpu"
DEVICE_CUDA = "cuda"

ACCELERATE_STRATEGY_DDP = "DDP"
ACCELERATE_STRATEGY_FSDP = "FSDP"
ACCELERATE_STRATEGY_DEEPSPEED = "DEEPSPEED"


class LoadConfig(BaseModel):
    trust_remote_code: bool = False
    # set Huggingface token to access dataset/model
    token: Optional[str] = None


class LoraConfig(BaseModel):
    task_type: str = "CAUSAL_LM"
    r: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: Optional[List[str]] = None


class GeneralConfig(BaseModel):
    base_model: str = None
    tokenizer_name: Optional[str] = None
    gaudi_config_name: Optional[str] = None
    gpt_base_model: bool = False
    output_dir: str = "./tmp"
    report_to: str = "none"
    resume_from_checkpoint: Optional[str] = None
    save_strategy: str = "no"
    config: LoadConfig = LoadConfig()
    lora_config: Optional[LoraConfig] = LoraConfig()
    enable_gradient_checkpointing: bool = False
    task: str = "instruction_tuning"

    @validator("report_to")
    def check_report_to(cls, v: str):
        assert v in ["none", "tensorboard"]
        return v

    @validator("task")
    def check_task(cls, v: str):
        assert v in ["instruction_tuning", "pretraining", "dpo", "rerank", "embedding"]
        return v


class DatasetConfig(BaseModel):
    train_file: str = None
    validation_file: Optional[str] = None
    validation_split_percentage: int = 5
    max_length: int = 512
    group: bool = True
    block_size: int = 512
    shuffle: bool = False
    max_source_length: int = 384
    max_prompt_length: int = 512
    padding_side: str = "right"
    truncation_side: str = "right"
    max_seq_length: int = 512
    truncation: bool = True
    padding: Union[bool, str] = True
    pad_to_max: bool = False
    mask_input: bool = True
    mask_response: bool = True
    data_preprocess_type: str = "neural_chat"
    max_train_samples: int = 0
    max_eval_samples: int = 0
    train_group_size: int = 8
    query_max_len: int = Field(
        default=128,
        description=(
            "The maximum total input sequence length after tokenization for passage. Sequences longer "
            "than this will be truncated, sequences shorter will be padded."
        ),
    )
    passage_max_len: int = Field(
        default=128,
        description=(
            "The maximum total input sequence length after tokenization for passage. Sequences longer "
            "than this will be truncated, sequences shorter will be padded."
        ),
    )
    query_instruction_for_retrieval: Optional[str] = Field(default=None, description="instruction for query")
    passage_instruction_for_retrieval: Optional[str] = Field(default=None, description="instruction for passage")


class RayResourceConfig(BaseModel):
    CPU: int = 32
    GPU: int = 0
    HPU: int = 0


class EmbeddingTrainingConfig(BaseModel):
    negatives_cross_device: bool = Field(default=False, description="share negatives across devices")
    temperature: Optional[float] = Field(default=0.02)
    sentence_pooling_method: str = Field(default="cls", description="the pooling method, should be cls or mean")
    normalized: bool = Field(default=True)
    use_inbatch_neg: bool = Field(default=True, description="use passages in the same batch as negatives")


class TrainingConfig(BaseModel):
    optimizer: str = "adamw_torch"
    batch_size: int = 2
    epochs: int = 1
    max_train_steps: Optional[int] = None
    learning_rate: float = 5.0e-5
    lr_scheduler: str = "linear"
    weight_decay: float = 0.0
    device: str = DEVICE_CPU
    hpu_execution_mode: str = "lazy"
    num_training_workers: int = 1
    resources_per_worker: RayResourceConfig = RayResourceConfig()
    accelerate_mode: str = ACCELERATE_STRATEGY_DDP
    mixed_precision: str = PRECISION_NO
    gradient_accumulation_steps: int = 1
    logging_steps: int = 10
    deepspeed_config_file: str = ""
    embedding_training_config: Optional[EmbeddingTrainingConfig] = EmbeddingTrainingConfig()
    dpo_beta: float = Field(default=0.1, description="the beta parameter for DPO loss")

    @validator("device")
    def check_device(cls, v: str):
        # will convert to lower case
        if v:
            assert v.lower() in [DEVICE_CPU, DEVICE_GPU, DEVICE_HPU, DEVICE_CUDA]
        return v.lower()

    @validator("hpu_execution_mode")
    def check_hpu_execution_mode(cls, v: str):
        if v:
            assert v in ["lazy", "eager", "eager.compile"]
        return v

    @validator("accelerate_mode")
    def check_accelerate_mode(cls, v: str):
        if v:
            assert v in [
                ACCELERATE_STRATEGY_DDP,
                ACCELERATE_STRATEGY_FSDP,
                ACCELERATE_STRATEGY_DEEPSPEED,
            ]
        return v

    @validator("mixed_precision")
    def check_mixed_precision(cls, v: str):
        if v:
            assert v in [PRECISION_BF16, PRECISION_FP16, PRECISION_NO]
        return v

    @validator("logging_steps")
    def check_logging_steps(cls, v: int):
        assert v > 0
        return v

    # @model_validator(mode='after')
    # def check_device_and_accelerate_mode(self) -> "Training":
    #     dev = self.device
    #     res = self.resources_per_worker
    #     mode = self.accelerate_mode
    #     if dev == "CPU":
    #         if res.GPU is not None and res.GPU > 0:
    #             raise ValueError("Please not specified GPU resource when use CPU only in Ray.")
    #         if mode != "CPU_DDP":
    #             raise ValueError("Please specified CPU related accelerate mode when use CPU only in Ray.")
    #     elif dev == "GPU":
    #         if res.GPU is None or res.GPU == 0:
    #             raise ValueError("Please specified GPU resource when use GPU to fine tune in Ray.")
    #         if mode not in ["GPU_DDP", "GPU_FSDP"]:
    #             raise ValueError("Please speicifed GPU related accelerate mode when use GPU to fine tune in Ray.")

    #     return self


class FinetuneConfig(BaseModel):
    General: GeneralConfig = GeneralConfig()
    Dataset: DatasetConfig = DatasetConfig()
    Training: TrainingConfig = TrainingConfig()


class FineTuningParams(FineTuningJobsRequest):
    # priority use FineTuningJobsRequest params
    General: GeneralConfig = GeneralConfig()
    Dataset: DatasetConfig = DatasetConfig()
    Training: TrainingConfig = TrainingConfig()
