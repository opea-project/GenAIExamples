# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference

from comps import EmbedDoc, ServiceType, TextDoc, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@embedding_tei_llamaindex",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
def embedding(input: TextDoc) -> EmbedDoc:
    embed_vector = embeddings._get_query_embedding(input.text)
    res = EmbedDoc(text=input.text, embedding=embed_vector)
    return res


if __name__ == "__main__":
    tei_embedding_model_name = os.getenv("TEI_EMBEDDING_MODEL_NAME", "BAAI/bge-large-en-v1.5")
    tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT", "http://localhost:8090")
    embeddings = TextEmbeddingsInference(model_name=tei_embedding_model_name, base_url=tei_embedding_endpoint)
    print("TEI Gaudi Embedding initialized.")
    opea_microservices["opea_service@embedding_tei_llamaindex"].start()
