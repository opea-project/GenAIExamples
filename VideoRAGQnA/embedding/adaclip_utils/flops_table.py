import sys
sys.path.insert(0, "../")

import torch
from embedding.adaclip_modeling.flops import SamplerFlops
from ptflops import get_model_complexity_info
from embedding.adaclip_modeling.clip_model import CLIP, build_model


feat_dim_dict = {
    "clip": 512,
    "frozen_clip": 512,
    "resnet18": 512,
    "resnet34": 512,
    "resnet50": 2048,
    "resnet101": 2048,
    "mobilenet_v2": 1280, 
    "mobilenet_v3_large": 1280,
    "resnext101_32x8d": 2048,
}


def get_gflops_params(backbone, cfg):

    macs = 0

    if backbone == "raw" or backbone == "clip":
        pass

    elif backbone in ["transformer", "lstm", "bilstm", "mlp"]:
        input_dim = cfg.rescale_size * cfg.rescale_size if cfg.policy_backbone == "raw" else feat_dim_dict[cfg.policy_backbone]
        input_dim = cfg.hidden_dim if (cfg.use_rnn and backbone == "mlp") else input_dim
        hidden_dim = cfg.mlp_hidden_dim if backbone == "mlp" else cfg.hidden_dim
        num_frm = cfg.num_frm if cfg.num_frm_subset <= 0 else min(cfg.num_frm, cfg.num_frm_subset)
        model = SamplerFlops(num_frm, cfg.policy_backbone, cfg.rnn, cfg.mlp_type, input_dim, hidden_dim)
        def prepare_inputs(res):
            feat = torch.rand((1, num_frm, input_dim)).float()
            return dict(input=feat, backbone=backbone)
        macs, _ = get_model_complexity_info(model, (1,), input_constructor=prepare_inputs, as_strings=False,
                                            print_per_layer_stat=False, verbose=False)

    elif backbone == "CLIP" or backbone == "frozen_clip":
        clip_state_dict = CLIP.get_config(pretrained_clip_name=cfg.clip_backbone)
        model = build_model(clip_state_dict).float()

        def prepare_inputs(res):
            image = torch.rand((1, 3, cfg.max_img_size, cfg.max_img_size)).float()
            return dict(image=image, text=None, flops=True)

        macs, _ = get_model_complexity_info(model, (1,), input_constructor=prepare_inputs, as_strings=False,
                                           print_per_layer_stat=False, verbose=False)

    else:
        num_frm = cfg.num_frm if cfg.num_frm_subset <= 0 else min(cfg.num_frm, cfg.num_frm_subset)
        model = SamplerFlops(num_frm, cfg.policy_backbone, cfg.rnn, cfg.mlp_type, feat_dim_dict[cfg.policy_backbone], cfg.hidden_dim)
        def prepare_inputs(res):
            image = torch.rand((num_frm, 3, cfg.max_img_size, cfg.max_img_size)).float()
            return dict(input=image, backbone=backbone)
        macs, _ = get_model_complexity_info(model, (1,), input_constructor=prepare_inputs, as_strings=False,
                                            print_per_layer_stat=False, verbose=False)

    gflops = macs / 1e9

    return gflops


if __name__ == "__main__":
    from types import SimpleNamespace
    cfg = {
        "max_img_size": 224,
        "policy_backbone": "mobilenet_v3_large",
        "hidden_dim": 512,
        "mlp_hidden_dim": 1024,
        "rescale_size": 56,
        "rnn": "transformer",
        "mlp_type": "mlp",
        "clip_backbone": "ViT-B/32",
        "use_rnn": True,
        "num_frm": 16,
        "num_frm_subset": 0
    }
    cfg = SimpleNamespace(**cfg)
    for model in ["CLIP", cfg.policy_backbone, cfg.rnn, "mlp"]:
        gflops = get_gflops_params(model, cfg)
        print("%-20s: %.4f GFLOPS" % (model, gflops))
