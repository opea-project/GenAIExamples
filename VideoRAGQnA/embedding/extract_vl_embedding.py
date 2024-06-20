import random
import argparse
import torch
import torch.backends.cudnn as cudnn
import numpy as np

from embedding.video_llama.common.config import Config
from embedding.video_llama.common.dist_utils import get_rank
from embedding.video_llama.common.registry import registry

class VLEmbeddingExtractor(object):
	"""docstring for VLEmbeddingExtractor"""
	def __init__(self, cfg_path, model_type):
		super(VLEmbeddingExtractor, self).__init__()
		args = argparse.Namespace(**{"cfg_path":cfg_path, "model_type":model_type, "options":[]})
		self.cfg = Config(args)
		self.setup_seeds()
		model_config = self.cfg.model_cfg
		print("vis_processor vit_precision:", model_config.get("vit_precision", "fp16"))
		if model_config.get("vit_precision", "fp16") == "fp16":
		    print("WARNING! FP16 not currently supported. Switching to FP32")
		    model_config['vit_precision'] = "fp32"
		model_cls = registry.get_model_class(model_config.arch)
		self.model = model_cls.from_config(model_config).to('cpu')
		self.model.eval()

	def setup_seeds(self):
	    seed = self.cfg.run_cfg.seed + get_rank()

	    print("Seed: ", seed)
	    random.seed(seed)
	    np.random.seed(seed)
	    torch.manual_seed(seed)

	    cudnn.benchmark = False
	    cudnn.deterministic = True
	    