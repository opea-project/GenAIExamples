# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from config import RANKER_MODEL
from fastrag.rankers import IPEXBiEncoderSimilarityRanker
from haystack import Document

from comps import CustomLogger
from comps.cores.mega.micro_service import ServiceType, opea_microservices, register_microservice
from comps.cores.proto.docarray import RerankedDoc, SearchedDoc, TextDoc

logger = CustomLogger("local_reranking")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@local_reranking",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=RerankedDoc,
)
def reranking(input: SearchedDoc) -> RerankedDoc:
    if logflag:
        logger.info(input)
    documents = []
    for i, d in enumerate(input.retrieved_docs):
        documents.append(Document(content=d.text, id=(i + 1)))
    sorted_documents = reranker_model.run(input.initial_query, documents)["documents"]
    ranked_documents = [TextDoc(id=doc.id, text=doc.content) for doc in sorted_documents]
    res = RerankedDoc(initial_query=input.initial_query, reranked_docs=ranked_documents)
    if logflag:
        logger.info(res)
    return res


if __name__ == "__main__":
    # Use an optimized quantized bi-encoder model for re-reranking
    reranker_model = IPEXBiEncoderSimilarityRanker(RANKER_MODEL)
    reranker_model.warm_up()

    opea_microservices["opea_service@local_reranking"].start()
