# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain_huggingface import HuggingFaceEmbeddings

from comps import EmbedDoc, ServiceType, TextDoc, opea_microservices, opea_telemetry, register_microservice


@register_microservice(
    name="opea_service@local_embedding",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
@opea_telemetry
def embedding(input: TextDoc) -> EmbedDoc:
    embed_vector = embeddings.embed_query(input.text)
    res = EmbedDoc(text=input.text, embedding=embed_vector)
    return res


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    opea_microservices["opea_service@local_embedding"].start()
