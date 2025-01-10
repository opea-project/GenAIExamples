# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import base64
import os
import tempfile
import threading

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, SDImg2ImgInputs, ServiceType

logger = CustomLogger("opea_imagetoimage")
logflag = os.getenv("LOGFLAG", False)

import torch
from diffusers import AutoPipelineForImage2Image
from diffusers.utils import load_image

pipe = None
args = None
initialization_lock = threading.Lock()
initialized = False


def initialize(
    model_name_or_path="stabilityai/stable-diffusion-xl-refiner-1.0",
    device="cpu",
    token=None,
    bf16=True,
    use_hpu_graphs=False,
):
    global pipe, args, initialized
    with initialization_lock:
        if not initialized:
            # initialize model and tokenizer
            if os.getenv("MODEL", None):
                model_name_or_path = os.getenv("MODEL")
            kwargs = {}
            if bf16:
                kwargs["torch_dtype"] = torch.bfloat16
            if not token:
                token = os.getenv("HF_TOKEN")
            if device == "hpu":
                kwargs(
                    {
                        "use_habana": True,
                        "use_hpu_graphs": use_hpu_graphs,
                        "gaudi_config": "Habana/stable-diffusion",
                        "token": token,
                    }
                )
                if "stable-diffusion-xl" in model_name_or_path:
                    from optimum.habana.diffusers import GaudiStableDiffusionXLImg2ImgPipeline

                    pipe = GaudiStableDiffusionXLImg2ImgPipeline.from_pretrained(
                        model_name_or_path,
                        **kwargs,
                    )
                else:
                    raise NotImplementedError(
                        "Only support stable-diffusion-xl now, " + f"model {model_name_or_path} not supported."
                    )
            elif device == "cpu":
                pipe = AutoPipelineForImage2Image.from_pretrained(model_name_or_path, token=token, **kwargs)
            else:
                raise NotImplementedError(f"Only support cpu and hpu device now, device {device} not supported.")
            logger.info("Stable Diffusion model initialized.")
            initialized = True


@OpeaComponentRegistry.register("OPEA_IMAGE2IMAGE")
class OpeaImageToImage(OpeaComponent):
    """A specialized ImageToImage component derived from OpeaComponent for Stable Diffusion model .

    Attributes:
        model_name_or_path (str): The name of the Stable Diffusion model used.
        device (str): which device to use.
        token(str): Huggingface Token.
        bf16(bool): Is use bf16.
        use_hpu_graphs(bool): Is use hpu_graphs.
    """

    def __init__(
        self,
        name: str,
        description: str,
        config: dict = None,
        seed=42,
        model_name_or_path="stabilityai/stable-diffusion-xl-refiner-1.0",
        device="cpu",
        token=None,
        bf16=True,
        use_hpu_graphs=False,
    ):
        super().__init__(name, ServiceType.IMAGE2IMAGE.name.lower(), description, config)
        initialize(
            model_name_or_path=model_name_or_path, device=device, token=token, bf16=bf16, use_hpu_graphs=use_hpu_graphs
        )
        self.pipe = pipe
        self.seed = seed
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaImageToImage health check failed.")

    async def invoke(self, input: SDImg2ImgInputs):
        """Invokes the ImageToImage service to generate Images for the provided input.

        Args:
            input (SDImg2ImgInputs): The input in SD images  format.
        """
        image = load_image(input.image).convert("RGB")
        prompt = input.prompt
        num_images_per_prompt = input.num_images_per_prompt

        generator = torch.manual_seed(self.seed)
        images = pipe(
            image=image, prompt=prompt, generator=generator, num_images_per_prompt=num_images_per_prompt
        ).images
        results = []
        with tempfile.TemporaryDirectory() as image_path:
            for i, image in enumerate(images):
                save_path = os.path.join(image_path, f"image_{i + 1}.png")
                image.save(save_path)
                with open(save_path, "rb") as f:
                    bytes = f.read()
                b64_str = base64.b64encode(bytes).decode()
                results.append(b64_str)

        return results

    def check_health(self) -> bool:
        """Checks the health of the ImageToImage service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        try:
            if self.pipe:
                return True
            else:
                return False
        except Exception as e:
            # Handle connection errors, timeouts, etc.
            logger.error(f"Health check failed: {e}")
        return False
