# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.tgi import OpeaDocSumTgi
from integrations.vllm import OpeaDocSumvLLM

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import DocSumChatCompletionRequest

logger = CustomLogger("llm_docsum")
logflag = os.getenv("LOGFLAG", False)

llm_component_name = os.getenv("DocSum_COMPONENT_NAME", "OpeaDocSumTgi")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(llm_component_name, description=f"OPEA LLM DocSum Component: {llm_component_name}")


@register_microservice(
    name="opea_service@llm_docsum",
    service_type=ServiceType.LLM,
    endpoint="/v1/docsum",
    host="0.0.0.0",
    port=9000,
)
@register_statistics(names=["opea_service@llm_docsum"])
async def llm_generate(input: DocSumChatCompletionRequest):
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(input)

    try:
        # Use the controller to invoke the active component
        response = await loader.invoke(input)
        # Record statistics
        statistics_dict["opea_service@llm_docsum"].append_latency(time.time() - start, None)
        return response

    except Exception as e:
        logger.error(f"Error during DocSum invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA DocSum Microservice is starting...")
    opea_microservices["opea_service@llm_docsum"].start()
