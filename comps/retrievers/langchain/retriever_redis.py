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
from langchain_community.vectorstores import Redis
from redis_config import INDEX_NAME, INDEX_SCHEMA, REDIS_URL

from comps import EmbedDoc768, SearchedDoc, TextDoc, opea_microservices, register_microservice


@register_microservice(name="opea_service@retriever_redis", expose_endpoint="/v1/retrieval", host="0.0.0.0", port=7000)
def retrieve(input: EmbedDoc768) -> SearchedDoc:
    embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    vector_db = Redis.from_existing_index(
        embedding=embeddings,
        index_name=INDEX_NAME,
        redis_url=REDIS_URL,
        schema=INDEX_SCHEMA,
    )
    search_res = vector_db.similarity_search_by_vector(embedding=input.embedding)
    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    return result


if __name__ == "__main__":
    opea_microservices["opea_service@retriever_redis"].start()
