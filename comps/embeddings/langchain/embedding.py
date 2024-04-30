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

from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from comps import EmbedDoc1024, TextDoc, opea_microservices, register_microservice


@register_microservice(
    name="opea_embedding_service",
    expose_endpoint="/v1/embeddings",
    port=9000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc1024,
)
def embedding(input: TextDoc) -> EmbedDoc1024:
    embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    embed_vector = embeddings.embed_query(input.text)
    res = EmbedDoc1024(text=input.text, embedding=embed_vector)
    return res


opea_microservices["opea_embedding_service"].start()
