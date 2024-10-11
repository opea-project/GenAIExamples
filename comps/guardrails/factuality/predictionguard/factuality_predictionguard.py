# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0


import time

from predictionguard import PredictionGuard

from comps import (
    FactualityDoc,
    ScoreDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@factuality_predictionguard",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/factuality",
    host="0.0.0.0",
    port=9075,
    input_datatype=FactualityDoc,
    output_datatype=ScoreDoc,
)
@register_statistics(names=["opea_service@factuality_predictionguard"])
def factuality_guard(input: FactualityDoc) -> ScoreDoc:
    start = time.time()

    client = PredictionGuard()

    reference = input.reference
    text = input.text

    result = client.factuality.check(reference=reference, text=text)

    statistics_dict["opea_service@factuality_predictionguard"].append_latency(time.time() - start, None)
    return ScoreDoc(score=result["checks"][0]["score"])


if __name__ == "__main__":
    print("Prediction Guard Factuality initialized.")
    opea_microservices["opea_service@factuality_predictionguard"].start()
