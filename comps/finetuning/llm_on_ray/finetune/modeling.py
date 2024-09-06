# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import torch
from torch import nn
from transformers import AutoModelForSequenceClassification, PreTrainedModel, TrainingArguments
from transformers.modeling_outputs import SequenceClassifierOutput

from comps.finetuning.finetune_config import DatasetConfig


class CrossEncoder(PreTrainedModel):
    def __init__(self, hf_model: PreTrainedModel, data_args: DatasetConfig, train_args: TrainingArguments):
        super().__init__(hf_model.config)
        self.hf_model = hf_model
        self.train_args = train_args
        self.data_args = data_args

        self.cross_entropy = nn.CrossEntropyLoss(reduction="mean")

        self.register_buffer("target_label", torch.zeros(self.train_args.per_device_train_batch_size, dtype=torch.long))

    def gradient_checkpointing_enable(self, **kwargs):
        self.hf_model.gradient_checkpointing_enable(**kwargs)

    def forward(self, **batch):
        ranker_out: SequenceClassifierOutput = self.hf_model(**batch, return_dict=True)
        logits = ranker_out.logits

        if self.training:
            scores = logits.view(-1, self.data_args.get("train_group_size", 8))
            loss = self.cross_entropy(scores, self.target_label[: scores.shape[0]])

            return SequenceClassifierOutput(
                loss=loss,
                **ranker_out,
            )
        else:
            return ranker_out

    @classmethod
    def from_pretrained(cls, data_args: DatasetConfig, train_args: TrainingArguments, *args, **kwargs):
        hf_model = AutoModelForSequenceClassification.from_pretrained(*args, **kwargs)
        reranker = cls(hf_model, data_args, train_args)
        return reranker

    def save_pretrained(self, output_dir: str, **kwargs):
        state_dict = self.hf_model.state_dict()
        state_dict = type(state_dict)({k: v.clone().cpu() for k, v in state_dict.items()})
        kwargs.pop("state_dict")
        self.hf_model.save_pretrained(output_dir, state_dict=state_dict, **kwargs)
