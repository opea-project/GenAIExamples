# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0

import time

from docarray import BaseDoc
from predictionguard import PredictionGuard

from comps import ServiceType, TextDoc, opea_microservices, register_microservice, register_statistics, statistics_dict


class LVMDoc(BaseDoc):
    image: str
    prompt: str
    max_new_tokens: int = 100
    top_k: int = 50
    top_p: float = 0.99
    temperature: float = 1.0


@register_microservice(
    name="opea_service@lvm_predictionguard",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9399,
    input_datatype=LVMDoc,
    output_datatype=TextDoc,
)
@register_statistics(names=["opea_service@lvm_predictionguard"])
async def lvm(request: LVMDoc) -> TextDoc:
    start = time.time()

    # make a request to the Prediction Guard API using the LlaVa model
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": request.prompt},
                {"type": "image_url", "image_url": {"url": request.image}},
            ],
        },
    ]
    result = client.chat.completions.create(
        model="llava-1.5-7b-hf",
        messages=messages,
        max_tokens=request.max_new_tokens,
        top_k=request.top_k,
        top_p=request.top_p,
        temperature=request.temperature,
    )

    statistics_dict["opea_service@lvm_predictionguard"].append_latency(time.time() - start, None)

    return TextDoc(text=result["choices"][0]["message"]["content"])


if __name__ == "__main__":
    client = PredictionGuard()
    opea_microservices["opea_service@lvm_predictionguard"].start()
