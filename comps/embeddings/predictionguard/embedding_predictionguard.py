# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0


import os
import time

from predictionguard import PredictionGuard

from comps import (
    EmbedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

# Initialize Prediction Guard client
client = PredictionGuard()


@register_microservice(
    name="opea_service@embedding_predictionguard",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
@register_statistics(names=["opea_service@embedding_predictionguard"])
def embedding(input: TextDoc) -> EmbedDoc:
    start = time.time()
    response = client.embeddings.create(model=pg_embedding_model_name, input=[{"text": input.text}])
    embed_vector = response["data"][0]["embedding"]
    embed_vector = embed_vector[:512]  # Keep only the first 512 elements
    res = EmbedDoc(text=input.text, embedding=embed_vector)
    statistics_dict["opea_service@embedding_predictionguard"].append_latency(time.time() - start, None)
    return res


if __name__ == "__main__":
    pg_embedding_model_name = os.getenv("PG_EMBEDDING_MODEL_NAME", "bridgetower-large-itm-mlm-itc")
    print("Prediction Guard Embedding initialized.")
    opea_microservices["opea_service@embedding_predictionguard"].start()
