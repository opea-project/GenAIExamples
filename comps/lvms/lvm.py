# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os
import time

import requests

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
    name="opea_service@lvm",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9399,
    input_datatype=LVMDoc,
    output_datatype=TextDoc,
)
@register_statistics(names=["opea_service@lvm"])
async def lvm(request: LVMDoc):
    start = time.time()
    img_b64_str = request.image
    prompt = request.prompt
    max_new_tokens = request.max_new_tokens

    inputs = {"img_b64_str": img_b64_str, "prompt": prompt, "max_new_tokens": max_new_tokens}

    # forward to the LLaVA server
    response = requests.post(url=f"{lvm_endpoint}/generate", data=json.dumps(inputs), proxies={"http": None})

    statistics_dict["opea_service@lvm"].append_latency(time.time() - start, None)
    return TextDoc(text=response.json()["text"])


if __name__ == "__main__":
    lvm_endpoint = os.getenv("LVM_ENDPOINT", "http://localhost:8399")

    print("[LVM] LVM initialized.")
    opea_microservices["opea_service@lvm"].start()
