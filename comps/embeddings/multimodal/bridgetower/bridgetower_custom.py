# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections import OrderedDict
from typing import List, Optional, Tuple, Union

import torch
import torch.nn.functional as F
from torch import nn
from torchvision import transforms
from torchvision.transforms import CenterCrop, Compose, Normalize, Resize, ToTensor
from transformers import BridgeTowerModel, BridgeTowerPreTrainedModel
from transformers.modeling_outputs import SequenceClassifierOutput
from transformers.models.bridgetower.modeling_bridgetower import (
    BridgeTowerContrastiveHead,
    BridgeTowerTextModel,
    BridgeTowerVisionModel,
)


class LayerNorm(nn.LayerNorm):
    """Subclass torch's LayerNorm to handle fp16."""

    def forward(self, x: torch.Tensor):
        orig_type = x.dtype
        ret = super().forward(x.type(torch.float32))
        return ret.type(orig_type)


class BridgeTowerImageFeatureExtractor(nn.Module):
    def __init__(
        self,
        patch_size=14,
        width=1024,
        resolution_after=294,
        ckpt_path=None,
    ):
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels=3, out_channels=width, kernel_size=patch_size, stride=patch_size, bias=False)

        scale = width**-0.5
        self.class_embedding = nn.Parameter(scale * torch.randn(width))
        self.positional_embedding = nn.Parameter(scale * torch.randn((resolution_after // patch_size) ** 2 + 1, width))
        self.ln_pre = LayerNorm(width)

        if ckpt_path is not None:
            sd = torch.load(ckpt_path)
            if "state_dict" in sd:
                sd = sd["state_dict"]
            print(f"Loading feature extractor checkpoint from {ckpt_path}")
            self.load_state_dict(sd)

    def forward(self, x: torch.Tensor):
        x = self.conv1(x)  # shape = [*, width, grid, grid]
        x = x.reshape(x.shape[0], x.shape[1], -1)  # shape = [*, width, grid ** 2]
        x = x.permute(0, 2, 1)  # shape = [*, grid ** 2, width]
        t = self.class_embedding.to(x.dtype) + torch.zeros(x.shape[0], 1, x.shape[-1], dtype=x.dtype, device=x.device)
        x = torch.cat([t, x], dim=1)  # shape = [*, grid ** 2 + 1, width]
        x = x + self.positional_embedding.to(x.dtype)
        x = self.ln_pre(x)
        x = x.permute(1, 0, 2)  # NLD -> LND
        return x


class BridgeTowerITCHead(nn.Module):
    def __init__(self, hidden_size, embed_size):
        super().__init__()
        self.fc = nn.Linear(hidden_size, embed_size)

    def forward(self, x):
        x = self.fc(x)
        return x


class _BridgeTowerTextModelWrapper(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.text_model = BridgeTowerTextModel(config)

    def forward(self, **kwargs):
        return self.text_model(**kwargs)


class _BridgeTowerVisionModelWrapper(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.vision_model = BridgeTowerVisionModel(config.vision_config)

        if config.share_cross_modal_transformer_layers:
            self.cross_modal_image_transform = nn.Linear(config.vision_config.hidden_size, config.hidden_size)
        else:
            self.cross_modal_image_transform = nn.ModuleList(
                [
                    nn.Linear(config.vision_config.hidden_size, config.hidden_size)
                    for _ in range(config.num_hidden_layers)
                ]
            )
        self.token_type_embeddings = nn.Embedding(2, config.hidden_size)

    def forward(self, **kwargs):
        return self.vision_model(**kwargs)


class BridgeTowerVisionFeatureExtractor(BridgeTowerPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)

        self.bridgetower = _BridgeTowerVisionModelWrapper(config)
        self.itc_image_head = BridgeTowerContrastiveHead(config.hidden_size, config.contrastive_hidden_size)

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.FloatTensor] = None,
        token_type_ids: Optional[torch.LongTensor] = None,
        head_mask: Optional[torch.FloatTensor] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        labels: Optional[torch.LongTensor] = None,
    ):

        outputs = self.bridgetower(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
        final_hidden_cls = outputs.hidden_states[-1][:, 0, :]

        image_embeds_with_ln = self.bridgetower.vision_model.visual.forward_post(final_hidden_cls)
        image_token_type_embeddings = self.bridgetower.token_type_embeddings(
            torch.full((1,), 1, dtype=torch.long, device=self.bridgetower.token_type_embeddings.weight.device)
        ).expand_as(image_embeds_with_ln)

        image_embeds = self.bridgetower.cross_modal_image_transform(image_embeds_with_ln) + image_token_type_embeddings

        final_hidden_cls = F.normalize(self.itc_image_head(image_embeds), dim=-1, p=2)

        return final_hidden_cls


class BridgeTowerTextFeatureExtractor(BridgeTowerPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)

        self.bridgetower = _BridgeTowerTextModelWrapper(config.text_config)
        self.itc_text_head = BridgeTowerITCHead(config.hidden_size, config.contrastive_hidden_size)

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.FloatTensor] = None,
        token_type_ids: Optional[torch.LongTensor] = None,
        head_mask: Optional[torch.FloatTensor] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        labels: Optional[torch.LongTensor] = None,
    ):

        outputs = self.bridgetower(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
        final_hidden_cls = outputs.hidden_states[-1][:, 0, :]
        final_hidden_cls = F.normalize(self.itc_text_head(final_hidden_cls), dim=-1, p=2)

        return final_hidden_cls


class BridgeTowerForITC(BridgeTowerPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)

        self.bridgetower = BridgeTowerModel(config)

        self.itc_text_head = BridgeTowerITCHead(config.hidden_size, config.contrastive_hidden_size)
        self.itc_image_head = BridgeTowerITCHead(config.hidden_size, config.contrastive_hidden_size)
        self.itc_cross_modal_head = BridgeTowerITCHead(config.hidden_size * 2, config.contrastive_hidden_size)

        # Initialize weights and apply final processing
        self.post_init()

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.FloatTensor] = None,
        token_type_ids: Optional[torch.LongTensor] = None,
        pixel_values: Optional[torch.FloatTensor] = None,
        pixel_mask: Optional[torch.LongTensor] = None,
        head_mask: Optional[torch.FloatTensor] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        image_embeds: Optional[torch.FloatTensor] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        labels: Optional[torch.LongTensor] = None,
    ) -> Union[SequenceClassifierOutput, Tuple[torch.FloatTensor]]:

        assert output_hidden_states, "output_hidden_states should be set to True for BridgeTowerForITC"
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        outputs = self.bridgetower(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            pixel_values=pixel_values,
            pixel_mask=pixel_mask,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            image_embeds=image_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        pooler_output = outputs.pooler_output if return_dict else outputs[2]

        hidden_states_txt, hidden_states_img, hidden_states_cross_modal = outputs.hidden_states

        final_hidden_txt = hidden_states_txt[-1]
        final_hidden_img = hidden_states_img[-1]

        image_embeds_with_ln = self.bridgetower.vision_model.visual.forward_post(final_hidden_img)
        image_token_type_embeddings = self.bridgetower.token_type_embeddings(
            torch.full((1,), 1, dtype=torch.long, device=self.bridgetower.token_type_embeddings.weight.device)
        ).expand_as(image_embeds_with_ln)

        final_hidden_img = (
            self.bridgetower.cross_modal_image_transform(image_embeds_with_ln) + image_token_type_embeddings
        )

        final_hidden_txt = F.normalize(self.itc_text_head(final_hidden_txt[:, 0, :]), dim=-1, p=2)
        final_hidden_img = F.normalize(self.itc_image_head(final_hidden_img[:, 0, :]), dim=-1, p=2)
        final_hidden_cross = F.normalize(self.itc_cross_modal_head(pooler_output), dim=-1, p=2)

        logits = torch.stack([final_hidden_txt, final_hidden_img, final_hidden_cross], dim=-2)

        if not return_dict:
            return tuple(logits)

        return SequenceClassifierOutput(
            loss=None,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )
