# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union

from integrations.tei import OpeaTEIReranking
from integrations.videoqna import OpeaVideoReranking

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import ChatCompletionRequest, RerankingRequest, RerankingResponse
from comps.cores.proto.docarray import LLMParamsDoc, LVMVideoDoc, RerankedDoc, SearchedDoc, SearchedMultimodalDoc

logger = CustomLogger("opea_reranking_microservice")
logflag = os.getenv("LOGFLAG", False)

rerank_component_name = os.getenv("RERANK_COMPONENT_NAME", "OPEA_TEI_RERANKING")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(rerank_component_name, description=f"OPEA RERANK Component: {rerank_component_name}")


@register_microservice(
    name="opea_service@reranking",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
)
@register_statistics(names=["opea_service@reranking"])
async def reranking(
    input: Union[SearchedMultimodalDoc, SearchedDoc, RerankingRequest, ChatCompletionRequest]
) -> Union[RerankedDoc, LLMParamsDoc, RerankingResponse, ChatCompletionRequest, LVMVideoDoc]:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        reranking_response = await loader.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {reranking_response}")

        # Record statistics
        statistics_dict["opea_service@reranking"].append_latency(time.time() - start, None)
        return reranking_response

    except Exception as e:
        logger.error(f"Error during reranking invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@reranking"].start()
    logger.info("OPEA Reranking Microservice is starting...")
