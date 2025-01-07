# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import export_to_video, load_image

from comps import CustomLogger, ImagesPath, OpeaComponent, OpeaComponentRegistry, ServiceType, VideoPath

logger = CustomLogger("opea")


@OpeaComponentRegistry.register("OPEA_IMAGE2VIDEO")
class OpeaImage2video(OpeaComponent):
    """A specialized image2video component derived from OpeaComponent for image2video services."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.IMAGE2VIDEO.name.lower(), description, config)

        # initialize model
        self.device = config["device"]
        self.seed = config["seed"]
        if self.device == "hpu":
            from optimum.habana.diffusers import GaudiEulerDiscreteScheduler, GaudiStableVideoDiffusionPipeline
            from optimum.habana.utils import set_seed

            set_seed(self.seed)
            scheduler = GaudiEulerDiscreteScheduler.from_pretrained(config["model_name_or_path"], subfolder="scheduler")
            kwargs = {
                "scheduler": scheduler,
                "use_habana": True,
                "use_hpu_graphs": config["use_hpu_graphs"],
                "gaudi_config": "Habana/stable-diffusion",
            }
            self.pipe = GaudiStableVideoDiffusionPipeline.from_pretrained(
                config["model_name_or_path"],
                **kwargs,
            )
        elif self.device == "cpu":
            self.pipe = StableVideoDiffusionPipeline.from_pretrained(config["model_name_or_path"])
        else:
            raise NotImplementedError(f"Only support cpu and hpu device now, device {self.device} not supported.")
        logger.info("Stable Video Diffusion model initialized.")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaImage2video health check failed.")

    async def invoke(self, input: ImagesPath) -> VideoPath:
        """Invokes the image2video service to generate video(s) for the provided input.

        Args:
            input (ImagesPath): The input for image2video service, including image paths.
        Returns:
            VideoPath: The response is path to the generated video.
        """
        logger.info("SVD generation begin.")
        images_path = [img_path.image_path for img_path in input.images_path]

        images = [load_image(img) for img in images_path]
        images = [image.resize((1024, 576)) for image in images]

        generator = torch.manual_seed(self.seed) if self.device == "cpu" else None
        frames = self.pipe(images, decode_chunk_size=8, generator=generator).frames[0]
        video_path = os.path.join(os.getcwd(), "generated.mp4")
        export_to_video(frames, video_path, fps=7)
        return VideoPath(video_path=video_path)

    def check_health(self) -> bool:
        return True
