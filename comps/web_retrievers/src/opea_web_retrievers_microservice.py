# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.google_search import OpeaGoogleSearch

from comps import (
    CustomLogger,
    EmbedDoc,
    OpeaComponentLoader,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_web_retriever_microservice")
logflag = os.getenv("LOGFLAG", False)

web_retriever_component_name = os.getenv("WEB_RETRIEVER_NAME", "OPEA_GOOGLE_SEARCH")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    web_retriever_component_name, description=f"OPEA WEB RETRIEVER Component: {web_retriever_component_name}"
)


@register_microservice(
    name="opea_service@web_retriever",
    service_type=ServiceType.WEB_RETRIEVER,
    endpoint="/v1/web_retrieval",
    host="0.0.0.0",
    port=7077,
    input_datatype=EmbedDoc,
    output_datatype=SearchedDoc,
)
@register_statistics(names=["opea_service@web_retriever", "opea_service@search"])
async def web_retriever(input: EmbedDoc) -> SearchedDoc:
    start = time.time()

    try:
        # Use the loader to invoke the active component
        res = await loader.invoke(input)
        if logflag:
            logger.info(res)
        statistics_dict["opea_service@web_retriever"].append_latency(time.time() - start, None)
        return res

    except Exception as e:
        logger.error(f"Error during web retriever invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA Web Retriever Microservice is starting....")
    opea_microservices["opea_service@web_retriever"].start()
