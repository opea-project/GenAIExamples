# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union

from integrations.opea import OPEALLM

from comps import (
    CustomLogger,
    LLMParamsDoc,
    OpeaComponentController,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import ChatCompletionRequest

logger = CustomLogger("llm")
logflag = os.getenv("LOGFLAG", False)

# Initialize OpeaComponentController
controller = OpeaComponentController()

# Register components
try:
    opea_llm = OPEALLM(
        name="OPEALLM",
        description="OPEA LLM Service, compatible with OpenAI API",
    )

    # Register components with the controller
    controller.register(opea_llm)

    # Discover and activate a healthy component
    controller.discover_and_activate()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")


@register_microservice(
    name="opea_service@llm",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=9000,
)
@register_statistics(names=["opea_service@llm"])
async def llm_generate(input: Union[LLMParamsDoc, ChatCompletionRequest, SearchedDoc]):
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(input)

    try:
        # Use the controller to invoke the active component
        response = await controller.invoke(input)
        # Record statistics
        statistics_dict["opea_service@llm"].append_latency(time.time() - start, None)
        return response

    except Exception as e:
        logger.error(f"Error during LLM invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA LLM Microservice is starting...")
    opea_microservices["opea_service@llm"].start()
