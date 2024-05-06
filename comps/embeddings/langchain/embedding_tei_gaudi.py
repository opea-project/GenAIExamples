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

from comps import EmbedDoc1024, TextDoc, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@embedding_tgi_gaudi",
    expose_endpoint="/v1/embeddings",
    port=8020,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
def safety_guard(input: TextDoc) -> TextDoc:
    embed_vector = embeddings.embed_query(input.text)
    res = EmbedDoc1024(text=input.text, embedding=embed_vector)
    return res


if __name__ == "__main__":
    tei_embedding_endpoint = os.getenv("TEI_ENDPOINT", "http://localhost:8080")
    embeddings = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    print("TEI Gaudi Embedding initialized.")
    opea_microservices["opea_service@embedding_tgi_gaudi"].start()
