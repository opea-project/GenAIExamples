# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
import time
from typing import Union

from integrations.milvus import OpeaMilvusRetriever
from integrations.redis import OpeaRedisRetriever

from comps import (
    CustomLogger,
    EmbedDoc,
    EmbedMultimodalDoc,
    OpeaComponentLoader,
    SearchedDoc,
    SearchedMultimodalDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResponseData,
)

logger = CustomLogger("opea_retrievers_microservice")
logflag = os.getenv("LOGFLAG", False)

retriever_component_name = os.getenv("RETRIEVER_COMPONENT_NAME", "OPEA_RETRIEVER_REDIS")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    retriever_component_name,
    description=f"OPEA RETRIEVER Component: {retriever_component_name}",
)


@register_microservice(
    name="opea_service@retrievers",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@register_statistics(names=["opea_service@retrievers"])
async def ingest_files(
    input: Union[EmbedDoc, EmbedMultimodalDoc, RetrievalRequest, ChatCompletionRequest]
) -> Union[SearchedDoc, SearchedMultimodalDoc, RetrievalResponse, ChatCompletionRequest]:
    start = time.time()

    if logflag:
        logger.info(f"[ retrieval ] input:{input}")

    try:
        # Use the loader to invoke the component
        response = await loader.invoke(input)

        # return different response format
        retrieved_docs = []
        if isinstance(input, EmbedDoc) or isinstance(input, EmbedMultimodalDoc):
            metadata_list = []
            for r in response:
                metadata_list.append(r.metadata)
                retrieved_docs.append(TextDoc(text=r.page_content))
            result = SearchedMultimodalDoc(
                retrieved_docs=retrieved_docs, initial_query=input.text, metadata=metadata_list
            )
        else:
            for r in response:
                retrieved_docs.append(RetrievalResponseData(text=r.page_content, metadata=r.metadata))
            if isinstance(input, RetrievalRequest):
                result = RetrievalResponse(retrieved_docs=retrieved_docs)
            elif isinstance(input, ChatCompletionRequest):
                input.retrieved_docs = retrieved_docs
                input.documents = [doc.text for doc in retrieved_docs]
                result = input

        # Record statistics
        statistics_dict["opea_service@retrievers"].append_latency(time.time() - start, None)

        if logflag:
            logger.info(f"[ retrieval ] Output generated: {response}")

        return result

    except Exception as e:
        logger.error(f"[ retrieval ] Error during retrieval invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA Retriever Microservice is starting...")
    opea_microservices["opea_service@retrievers"].start()
