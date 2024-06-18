import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F

from embedding.adaclip_modeling import clip
from einops import rearrange
from embedding.adaclip_utils.flops_table import feat_dim_dict
from embedding.adaclip_modeling.clip_model import Transformer
from embedding.adaclip_modeling.gumbel_softmax import gumbel_softmax_top_k


class Sampler(nn.Module):
    def __init__(self, cfg, clip_embed_dim):
        super().__init__()

        self.num_frm = cfg.num_frm
        self.policy_backbone = cfg.policy_backbone
        self.use_rnn = cfg.use_rnn
        self.rnn_type = cfg.rnn
        self.top_k = cfg.top_k

        if cfg.policy_backbone == "resnet50":
            self.cnn_model = torchvision.models.resnet50(weights=torchvision.models.ResNet50_Weights.DEFAULT)
            last_layer = "fc"
            setattr(self.cnn_model, last_layer, nn.Sequential())
        elif cfg.policy_backbone == "mobilenet_v2":
            self.cnn_model = torchvision.models.mobilenet_v2(weights=torchvision.models.MobileNet_V2_Weights.DEFAULT)
            last_layer = "classifier"
            setattr(self.cnn_model, last_layer, nn.Sequential())
        elif cfg.policy_backbone == "mobilenet_v3_large":
            self.cnn_model = torchvision.models.mobilenet_v3_large(weights=torchvision.models.MobileNet_V3_Large_Weights.DEFAULT)
            last_layer = "classifier"
            self.cnn_model.classifier[2] = nn.Sequential()
            self.cnn_model.classifier[3] = nn.Sequential()
        elif cfg.policy_backbone == "raw":
            self.cnn_model = None
            backbone_channel_in_size = cfg.rescale_size * cfg.rescale_size
        elif cfg.policy_backbone == "clip":
            self.cnn_model = None
            backbone_channel_in_size = clip_embed_dim
        elif cfg.policy_backbone == "frozen_clip":
            self.cnn_model = None
            self.frozen_clip, _ = clip.load(cfg.clip_backbone)
            for _, p in self.frozen_clip.named_parameters():
                p.requires_grad = False
            backbone_channel_in_size = clip_embed_dim

        if self.cnn_model is not None:
            backbone_channel_in_size = feat_dim_dict[cfg.policy_backbone]

        if self.use_rnn:
            if self.rnn_type == "transformer":
                transformer_width = cfg.hidden_dim
                transformer_heads = transformer_width // 64
                self.projection = self.prepare_linear(backbone_channel_in_size, transformer_width, None, "fc")
                self.frame_position_embeddings = nn.Embedding(cfg.num_frm, transformer_width)
                self.transformer = Transformer(width=transformer_width, layers=1, heads=transformer_heads)
            elif self.rnn_type == "lstm":
                self.rnn = nn.LSTM(input_size=backbone_channel_in_size, hidden_size=cfg.hidden_dim, bias=True, batch_first=True, bidirectional=False)
            elif self.rnn_type == "bilstm":
                self.rnn = nn.LSTM(input_size=backbone_channel_in_size, hidden_size=cfg.hidden_dim, bias=True, batch_first=True, bidirectional=True)

        input_dim = cfg.hidden_dim if self.use_rnn else backbone_channel_in_size
        self.linear = self.prepare_linear(input_dim, 1, cfg.mlp_hidden_dim, cfg.mlp_type)

    def prepare_linear(self, input_dim, output_dim, hidden_dim, mlp_type):
        if mlp_type == "fc":
            linear_model = nn.Sequential(nn.Linear(input_dim, output_dim))
        elif mlp_type == "mlp":
            linear_model = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, output_dim)
            )
        for module in linear_model:
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight)
                nn.init.constant_(module.bias, 0)
        return linear_model

    def get_policy_actions(self, visual_inputs, tau):

        if self.cnn_model is not None:
            #print("policy_backbone:", self.policy_backbone)
            #print("use_rnn:", self.use_rnn)
            #print("rnn_type:", self.rnn_type)
            #print("visual_inputs input to cnn_model:", visual_inputs[0,0,:2,:2])
            feat_lite = self.cnn_model(visual_inputs) # (b * n_frms, feat_dim)
            #print("feat_lite in cnn_model:", feat_lite[0,:3])
        elif self.policy_backbone == "clip":
            feat_lite = visual_inputs
        elif self.policy_backbone == "frozen_clip":
            feat_lite = self.frozen_clip.encode_image(visual_inputs).float()
        elif self.policy_backbone == "raw":
            feat_lite = visual_inputs
        feat_lite = rearrange(feat_lite, "(b n) d -> b n d", n=self.num_frm)
        #print("feat_lite after rearrange:", feat_lite[:,0,:3])
        if self.use_rnn:
            if self.rnn_type == "transformer":
                feat_lite = self.projection(feat_lite)
                position_ids = torch.arange(self.num_frm, dtype=torch.long, device=feat_lite.device)
                position_ids = position_ids.unsqueeze(0).expand(feat_lite.size(0), -1)
                frame_position_embeddings = self.frame_position_embeddings(position_ids)
                feat_lite = feat_lite + frame_position_embeddings
                feat_lite = feat_lite.permute(1, 0, 2)
                feat_lite = self.transformer(feat_lite)
                feat_lite = feat_lite.permute(1, 0, 2)
            elif self.rnn_type == "lstm":
                feat_lite, _ = self.rnn(feat_lite)
            elif self.rnn_type == "bilstm":
                feat_lite, _ = self.rnn(feat_lite)
                feat_lite = rearrange(feat_lite, "b n (l d) -> b n l d", l=2)
                feat_lite = torch.mean(feat_lite, dim=2)
        #print(f"feat_lite after rnn {self.use_rnn} type:{self.rnn_type} :", feat_lite[:,0,:3])
        logits = self.linear(feat_lite).squeeze(-1)
        #print("logits.shape:", logits.shape)
        #print("logits:", logits[:,:3])
        if self.training:
            prob = torch.log(F.softmax(logits, dim=-1).clamp(min=1e-8))
            actions = gumbel_softmax_top_k(prob, int(self.top_k), tau, True, reduce_sum=False) # B, K, N
        else:
            index = torch.argsort(logits, dim=-1, descending=True)[:, :self.top_k]
            actions = F.one_hot(index, num_classes=logits.shape[-1]).to(logits.dtype) # B, K, N
        return actions, logits

    def forward(self, policy_inputs, tau=1):
        if self.policy_backbone != "clip":
            policy_inputs = rearrange(policy_inputs, "b n c h w -> (b n) c h w")
            if self.policy_backbone == "raw":
                policy_inputs = rearrange(policy_inputs, "b c h w -> b (c h w)")
        actions, logits = self.get_policy_actions(policy_inputs, tau)
        return actions, logits

    def freeze_cnn_backbone(self):
        if self.cnn_model is not None:
            for _, p in self.cnn_model.named_parameters():
                p.requires_grad = False
