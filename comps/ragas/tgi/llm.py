# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from datasets import Dataset
from langchain_community.embeddings import (
    HuggingFaceBgeEmbeddings,
    HuggingFaceEmbeddings,
    HuggingFaceHubEmbeddings,
    HuggingFaceInstructEmbeddings,
)
from langchain_community.llms import HuggingFaceEndpoint
from langsmith import traceable
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from comps import GeneratedDoc, RAGASParams, RAGASScores, ServiceType, opea_microservices, register_microservice

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")


@register_microservice(
    name="opea_service@ragas_tgi_llm",
    service_type=ServiceType.RAGAS,
    endpoint="/v1/ragas",
    host="0.0.0.0",
    port=9050,
    input_datatype=RAGASParams,
    output_datatype=RAGASScores,
)
@traceable(run_type="llm")
def llm_generate(input: RAGASParams):
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")

    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint,
        max_new_tokens=input.max_new_tokens,
        top_k=input.top_k,
        top_p=input.top_p,
        typical_p=input.typical_p,
        temperature=input.temperature,
        repetition_penalty=input.repetition_penalty,
        streaming=input.streaming,
        timeout=600,
    )

    data_collections = {
        "question": input.questions,
        "answer": input.answers,
        "docs": input.docs,
        "ground_truth": input.groundtruths,
    }
    dataset = Dataset.from_dict(data_collections)

    score = evaluate(
        dataset,
        metrics=[answer_relevancy, faithfulness, context_recall, context_precision],
        llm=llm,
        embeddings=embedder,
    )
    df = score.to_pandas()
    answer_relevancy_average = df["answer_relevancy"][:].mean()
    faithfulness_average = df["faithfulness"][:].mean()
    context_recall_average = df["context_recall"][:].mean()
    context_precision_average = df["context_precision"][:].mean()

    return RAGASScores(
        answer_relevancy=answer_relevancy_average,
        faithfulness=faithfulness_average,
        context_recallL=context_recall_average,
        context_precision=context_precision_average,
    )


if __name__ == "__main__":
    opea_microservices["opea_service@llm_tgi"].start()
