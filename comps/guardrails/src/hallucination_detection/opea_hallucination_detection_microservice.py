# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union

from integrations.hallucination_guard import OpeaHallucinationGuard

from comps import (
    CustomLogger,
    GeneratedDoc,
    LLMParamsDoc,
    OpeaComponentLoader,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import ChatCompletionRequest

logger = CustomLogger("opea_hallucination_detection_microservice")
logflag = os.getenv("LOGFLAG", False)

hallucination_detection_component_name = os.getenv("HALLUCINATION_DETECTION_COMPONENT_NAME", "OPEA_HALLUCINATION_GUARD")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    hallucination_detection_component_name,
    name=hallucination_detection_component_name,
    description=f"OPEA Hallucination Detection Component: {hallucination_detection_component_name}",
)


@register_microservice(
    name="opea_service@hallucination_detection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/hallucination_detection",
    host="0.0.0.0",
    port=9000,
)
@register_statistics(names=["opea_service@hallucination_detection"])
async def hallucination_guard(input: Union[LLMParamsDoc, ChatCompletionRequest, SearchedDoc]):
    start = time.time()
    if logflag:
        logger.info(input)

    try:
        hallucination_response = await loader.invoke(input)

        if logflag:
            logger.info(hallucination_response)

        statistics_dict["opea_service@hallucination_detection"].append_latency(time.time() - start, None)
        return hallucination_response
    except Exception as e:
        logger.error(f"Error during hallucination detection invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@hallucination_detection"].start()
    logger.info("Hallucination Detection Microservice is up and running successfully...")
