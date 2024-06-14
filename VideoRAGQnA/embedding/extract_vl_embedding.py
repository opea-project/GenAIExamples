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
	def __init__(self, cfg_path, gpu_id, model_type):
		super(VLEmbeddingExtractor, self).__init__()
		args = argparse.Namespace(**{"cfg_path":cfg_path, "gpu_id":gpu_id, "model_type":model_type, "options":[]})
		self.cfg = Config(args)
		self.setup_seeds()
		model_config = self.cfg.model_cfg
		model_config.device_8bit = args.gpu_id
		model_cls = registry.get_model_class(model_config.arch)
		self.model = model_cls.from_config(model_config).to('cuda:{}'.format(args.gpu_id))
		self.model.eval()

	def setup_seeds(self):
	    seed = self.cfg.run_cfg.seed + get_rank()

	    print("Seed: ", seed)
	    random.seed(seed)
	    np.random.seed(seed)
	    torch.manual_seed(seed)

	    cudnn.benchmark = False
	    cudnn.deterministic = True
	    