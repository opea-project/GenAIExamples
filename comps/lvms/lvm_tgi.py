# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from huggingface_hub import InferenceClient

from comps import (
    LVMDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@lvm_tgi",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9399,
    input_datatype=LVMDoc,
    output_datatype=TextDoc,
)
@register_statistics(names=["opea_service@lvm_tgi"])
async def lvm(request: LVMDoc):
    start = time.time()
    img_b64_str = request.image
    prompt = request.prompt
    max_new_tokens = request.max_new_tokens

    image = f"data:image/png;base64,{img_b64_str}"
    image_prompt = f"![]({image})\nUSER: {prompt}\nASSISTANT:"
    generated_str = lvm_client.text_generation(image_prompt, max_new_tokens=max_new_tokens)
    statistics_dict["opea_service@lvm_tgi"].append_latency(time.time() - start, None)
    return TextDoc(text=generated_str)


if __name__ == "__main__":
    lvm_endpoint = os.getenv("LVM_ENDPOINT", "http://localhost:8399")
    lvm_client = InferenceClient(lvm_endpoint)
    print("[LVM] LVM initialized.")
    opea_microservices["opea_service@lvm_tgi"].start()
