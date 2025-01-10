# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import os
import tempfile

import torch
from diffusers import DiffusionPipeline

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, SDInputs, SDOutputs, ServiceType

logger = CustomLogger("opea")


@OpeaComponentRegistry.register("OPEA_TEXT2IMAGE")
class OpeaText2image(OpeaComponent):
    """A specialized text2image component derived from OpeaComponent for text2image services.

    Attributes:
        client (AsyncInferenceClient): An instance of the async client for embedding generation.
        model_name (str): The name of the embedding model used.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.TEXT2IMAGE.name.lower(), description, config)

        # initialize model and tokenizer
        self.seed = config["seed"]
        model_name_or_path = config["model_name_or_path"]
        device = config["device"]
        if os.getenv("MODEL", None):
            model_name_or_path = os.getenv("MODEL")
        kwargs = {}
        if config["bf16"]:
            kwargs["torch_dtype"] = torch.bfloat16
        if not config["token"]:
            config["token"] = os.getenv("HF_TOKEN")
        if device == "hpu":
            kwargs.update(
                {
                    "use_habana": True,
                    "use_hpu_graphs": config["use_hpu_graphs"],
                    "gaudi_config": "Habana/stable-diffusion",
                    "token": config["token"],
                }
            )
            if "stable-diffusion-3" in model_name_or_path:
                from optimum.habana.diffusers import GaudiStableDiffusion3Pipeline

                self.pipe = GaudiStableDiffusion3Pipeline.from_pretrained(
                    model_name_or_path,
                    **kwargs,
                )
            elif "stable-diffusion" in model_name_or_path.lower() or "flux" in model_name_or_path.lower():
                from optimum.habana.diffusers import AutoPipelineForText2Image

                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    model_name_or_path,
                    **kwargs,
                )
            else:
                raise NotImplementedError(
                    "Only support stable-diffusion, stable-diffusion-xl, stable-diffusion-3 and flux now, "
                    + f"model {model_name_or_path} not supported."
                )
        elif device == "cpu":
            self.pipe = DiffusionPipeline.from_pretrained(model_name_or_path, token=config["token"], **kwargs)
        else:
            raise NotImplementedError(f"Only support cpu and hpu device now, device {device} not supported.")
        logger.info("Stable Diffusion model initialized.")

    async def invoke(self, input: SDInputs) -> SDOutputs:
        """Invokes the text2image service to generate image(s) for the provided input.

        Args:
            input (SDInputs): The input for text2image service, including prompt and optional parameters like num_images_per_prompt.

        Returns:
            SDOutputs: The response is a list of images.
        """
        prompt = input.prompt
        num_images_per_prompt = input.num_images_per_prompt

        generator = torch.manual_seed(self.seed)
        images = self.pipe(prompt, generator=generator, num_images_per_prompt=num_images_per_prompt).images
        with tempfile.TemporaryDirectory() as image_path:
            results = []
            for i, image in enumerate(images):
                save_path = os.path.join(image_path, f"image_{i+1}.png")
                image.save(save_path)
                with open(save_path, "rb") as f:
                    bytes = f.read()
                b64_str = base64.b64encode(bytes).decode()
                results.append(b64_str)
        return SDOutputs(images=results)

    def check_health(self) -> bool:
        return True
