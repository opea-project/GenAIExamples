# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from langchain_community.embeddings import HuggingFaceHubEmbeddings

from comps import EmbedDoc768, ServiceType, TextDoc, opea_microservices, opea_telemetry, register_microservice


@register_microservice(
    name="opea_service@embedding_tgi_gaudi",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc768,
)
@opea_telemetry
def embedding(input: TextDoc) -> EmbedDoc768:
    embed_vector = embeddings.embed_query(input.text)
    embed_vector = embed_vector[:768]  # Keep only the first 768 elements
    res = EmbedDoc768(text=input.text, embedding=embed_vector)
    return res


if __name__ == "__main__":
    tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT", "http://localhost:8080")
    embeddings = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    print("TEI Gaudi Embedding initialized.")
    opea_microservices["opea_service@embedding_tgi_gaudi"].start()
