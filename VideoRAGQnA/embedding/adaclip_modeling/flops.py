import torch
import torchvision
import torch.nn as nn
from einops import rearrange
from embedding.adaclip_modeling.clip_model import Transformer


class SamplerFlops(nn.Module):
    def __init__(self, num_frm, policy_backbone, rnn_type, mlp_type, input_dim, hidden_dim):
        super().__init__()

        self.num_frm = num_frm
        self.rnn_type = rnn_type

        if policy_backbone == "resnet50":
            self.cnn_model = torchvision.models.resnet50(weights=torchvision.models.ResNet50_Weights.DEFAULT)
            last_layer = "fc"
            setattr(self.cnn_model, last_layer, nn.Sequential())
        elif policy_backbone == "mobilenet_v2":
            self.cnn_model = torchvision.models.mobilenet_v2(weights=torchvision.models.MobileNet_V2_Weights.DEFAULT)
            last_layer = "classifier"
            setattr(self.cnn_model, last_layer, nn.Sequential())
        elif policy_backbone == "mobilenet_v3_large":
            self.cnn_model = torchvision.models.mobilenet_v3_large(weights=torchvision.models.MobileNet_V3_Large_Weights.DEFAULT)
            last_layer = "classifier"
            self.cnn_model.classifier[2] = nn.Sequential()
            self.cnn_model.classifier[3] = nn.Sequential()
        else:
            self.cnn_model = None

        if self.rnn_type == "transformer":
            transformer_width = hidden_dim
            transformer_heads = transformer_width // 64
            self.projection = self.prepare_linear(input_dim, transformer_width, None, "fc")
            self.frame_position_embeddings = nn.Embedding(self.num_frm, transformer_width)
            self.transformer = Transformer(width=transformer_width, layers=1, heads=transformer_heads)
        elif self.rnn_type == "lstm":
            self.rnn = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, bias=True, batch_first=True, bidirectional=False)
        elif self.rnn_type == "bilstm":
            self.rnn = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, bias=True, batch_first=True, bidirectional=True)

        self.linear = self.prepare_linear(input_dim, 1, hidden_dim, mlp_type)

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

    def get_cnn_flops(self, visual_inputs):
        if self.cnn_model is not None:
            return self.cnn_model(visual_inputs) # (b * n_frms, feat_dim)

    def get_rnn_flops(self, feat_lite):

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
        return

    def get_mlp_flops(self, feat_lite):
        return self.linear(feat_lite).squeeze(-1)

    def forward(self, input, backbone):
        if backbone == "mlp":
            return self.get_mlp_flops(input)
        elif backbone in ["transformer", "lstm", "bilstm"]:
            return self.get_rnn_flops(input)
        else:
            return self.get_cnn_flops(input)
