# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, Optional

import torch
import torch.distributed as dist
from torch import nn
from transformers import AutoModel, AutoModelForSequenceClassification, PreTrainedModel
from transformers.modeling_outputs import MaskedLMOutput, SequenceClassifierOutput

from comps import CustomLogger

logger = CustomLogger("llm_on_ray/finetune/modeling")


class CrossEncoder(PreTrainedModel):
    def __init__(self, hf_model: PreTrainedModel, train_group_size: int, batch_size: int):
        super().__init__(hf_model.config)
        self.hf_model = hf_model
        self.train_group_size = train_group_size
        self.batch_size = batch_size

        self.cross_entropy = nn.CrossEntropyLoss(reduction="mean")

        self.register_buffer("target_label", torch.zeros(self.batch_size, dtype=torch.long))

    def gradient_checkpointing_enable(self, **kwargs):
        self.hf_model.gradient_checkpointing_enable(**kwargs)

    def forward(self, **batch):
        ranker_out: SequenceClassifierOutput = self.hf_model(**batch, return_dict=True)
        logits = ranker_out.logits

        if self.training:
            scores = logits.view(-1, self.train_group_size)
            loss = self.cross_entropy(scores, self.target_label[: scores.shape[0]])

            return SequenceClassifierOutput(
                loss=loss,
                **ranker_out,
            )
        else:
            return ranker_out

    @classmethod
    def from_pretrained(cls, train_group_size: int, batch_size: int, *args, **kwargs):
        hf_model = AutoModelForSequenceClassification.from_pretrained(*args, **kwargs)
        reranker = cls(hf_model, train_group_size, batch_size)
        return reranker

    def save_pretrained(self, output_dir: str, **kwargs):
        state_dict = self.hf_model.state_dict()
        state_dict = type(state_dict)({k: v.clone().cpu() for k, v in state_dict.items()})
        kwargs.pop("state_dict")
        self.hf_model.save_pretrained(output_dir, state_dict=state_dict, **kwargs)


class BiEncoderModel(nn.Module):
    TRANSFORMER_CLS = AutoModel

    def __init__(
        self,
        model_name: str = None,
        should_concat: bool = False,
        normalized: bool = False,
        sentence_pooling_method: str = "cls",
        negatives_cross_device: bool = False,
        temperature: float = 1.0,
        use_inbatch_neg: bool = True,
    ):
        super().__init__()
        self.model = AutoModel.from_pretrained(model_name, add_pooling_layer=False)
        self.cross_entropy = nn.CrossEntropyLoss(reduction="mean")

        self.should_concat = should_concat
        self.normalized = normalized
        self.sentence_pooling_method = sentence_pooling_method
        self.temperature = temperature
        self.use_inbatch_neg = use_inbatch_neg
        self.config = self.model.config

        if not normalized:
            self.temperature = 1.0
            logger.info("reset temperature = 1.0 due to using inner product to compute similarity")
        if normalized:
            if self.temperature > 0.5:
                raise ValueError(
                    "Temperature should be smaller than 1.0 when use cosine similarity (i.e., normalized=True). Recommend to set it 0.01-0.1"
                )

        self.negatives_cross_device = negatives_cross_device
        if self.negatives_cross_device:
            if not dist.is_initialized():
                raise ValueError("Distributed training has not been initialized for representation all gather.")
            #     logger.info("Run in a single GPU, set negatives_cross_device=False")
            #     self.negatives_cross_device = False
            # else:
            self.process_rank = dist.get_rank()
            self.world_size = dist.get_world_size()

    def gradient_checkpointing_enable(self, **kwargs):
        self.model.gradient_checkpointing_enable(**kwargs)

    def sentence_embedding(self, hidden_state, mask):
        if self.sentence_pooling_method == "mean":
            s = torch.sum(hidden_state * mask.unsqueeze(-1).float(), dim=1)
            d = mask.sum(axis=1, keepdim=True).float()
            return s / d
        elif self.sentence_pooling_method == "cls":
            return hidden_state[:, 0]

    def encode(self, features):
        if features is None:
            return None
        psg_out = self.model(**features, return_dict=True)
        p_reps = self.sentence_embedding(psg_out.last_hidden_state, features["attention_mask"])
        if self.normalized:
            p_reps = torch.nn.functional.normalize(p_reps, dim=-1)
        return p_reps.contiguous()

    def encode_concat(self, query, passage):
        if query is None or passage is None:
            return None

        batch_size = query["input_ids"].size()[0]

        psg_out = self.model(
            input_ids=torch.cat([query["input_ids"], passage["input_ids"]]),
            attention_mask=torch.cat([query["attention_mask"], passage["attention_mask"]]),
            return_dict=True,
        )
        reps = self.sentence_embedding(
            psg_out.last_hidden_state, torch.cat([query["attention_mask"], passage["attention_mask"]])
        )
        if self.normalized:
            reps = torch.nn.functional.normalize(reps, dim=-1)

        q_reps = reps[:batch_size]
        p_reps = reps[batch_size:]

        return q_reps.contiguous(), p_reps.contiguous()

    def compute_similarity(self, q_reps, p_reps):
        if len(p_reps.size()) == 2:
            return torch.matmul(q_reps, p_reps.transpose(0, 1))
        return torch.matmul(q_reps, p_reps.transpose(-2, -1))

    def forward(self, query: Dict[str, torch.Tensor] = None, passage: Dict[str, torch.Tensor] = None):
        if self.should_concat:
            q_reps, p_reps = self.encode_concat(query, passage)
        else:
            q_reps = self.encode(query)
            p_reps = self.encode(passage)

        if self.training:
            if self.negatives_cross_device and self.use_inbatch_neg:
                q_reps = self._dist_gather_tensor(q_reps)
                p_reps = self._dist_gather_tensor(p_reps)

            group_size = p_reps.size(0) // q_reps.size(0)
            if self.use_inbatch_neg:
                scores = self.compute_similarity(q_reps, p_reps) / self.temperature  # B B*G
                scores = scores.view(q_reps.size(0), -1)

                target = torch.arange(scores.size(0), device=scores.device, dtype=torch.long)
                target = target * group_size
                loss = self.compute_loss(scores, target)
            else:
                scores = (
                    self.compute_similarity(
                        q_reps[
                            :,
                            None,
                            :,
                        ],
                        p_reps.view(q_reps.size(0), group_size, -1),
                    ).squeeze(1)
                    / self.temperature
                )  # B G

                scores = scores.view(q_reps.size(0), -1)
                target = torch.zeros(scores.size(0), device=scores.device, dtype=torch.long)
                loss = self.compute_loss(scores, target)

        else:
            scores = self.compute_similarity(q_reps, p_reps)
            loss = None

        return MaskedLMOutput(loss=loss, logits=None, hidden_states=None, attentions=None)

    def compute_loss(self, scores, target):
        return self.cross_entropy(scores, target)

    def _dist_gather_tensor(self, t: Optional[torch.Tensor]):
        if t is None:
            return None
        t = t.contiguous()

        all_tensors = [torch.empty_like(t) for _ in range(self.world_size)]
        dist.all_gather(all_tensors, t)

        all_tensors[self.process_rank] = t
        all_tensors = torch.cat(all_tensors, dim=0)

        return all_tensors

    def save(self, output_dir: str):
        state_dict = self.model.state_dict()
        state_dict = type(state_dict)({k: v.clone().cpu() for k, v in state_dict.items()})
        self.model.save_pretrained(output_dir, state_dict=state_dict)
