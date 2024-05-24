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

from langsmith import traceable
from sentence_transformers import CrossEncoder

from comps import RerankedDoc, SearchedDoc, ServiceType, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@local_reranking",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=RerankedDoc,
)
@traceable(run_type="llm")
def reranking(input: SearchedDoc) -> RerankedDoc:
    query_and_docs = [(input.initial_query, doc.text) for doc in input.retrieved_docs]
    scores = reranker_model.predict(query_and_docs)
    first_passage = sorted(list(zip(input.retrieved_docs, scores)), key=lambda x: x[1], reverse=True)[0][0]
    res = RerankedDoc(query=input.query, doc=first_passage)
    return res


if __name__ == "__main__":
    reranker_model = CrossEncoder(model_name="BAAI/bge-reranker-large", max_length=512)
    opea_microservices["opea_service@local_reranking"].start()
