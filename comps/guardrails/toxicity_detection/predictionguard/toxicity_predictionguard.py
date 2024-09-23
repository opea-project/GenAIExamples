# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0


import time

from docarray import BaseDoc
from predictionguard import PredictionGuard

from comps import ServiceType, TextDoc, opea_microservices, register_microservice, register_statistics, statistics_dict


class ScoreDoc(BaseDoc):
    score: float


@register_microservice(
    name="opea_service@toxicity_predictionguard",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/toxicity",
    host="0.0.0.0",
    port=9090,
    input_datatype=TextDoc,
    output_datatype=ScoreDoc,
)
@register_statistics(names=["opea_service@toxicity_predictionguard"])
def toxicity_guard(input: TextDoc) -> ScoreDoc:
    start = time.time()

    client = PredictionGuard()

    text = input.text

    result = client.toxicity.check(text=text)

    statistics_dict["opea_service@toxicity_predictionguard"].append_latency(time.time() - start, None)
    return ScoreDoc(score=result["checks"][0]["score"])


if __name__ == "__main__":
    print("Prediction Guard Toxicity initialized.")
    opea_microservices["opea_service@toxicity_predictionguard"].start()
