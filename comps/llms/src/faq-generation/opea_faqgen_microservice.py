# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.tgi import OPEAFAQGen_TGI
from integrations.vllm import OPEAFAQGen_vLLM

from comps import (
    CustomLogger,
    LLMParamsDoc,
    OpeaComponentLoader,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("llm_faqgen")
logflag = os.getenv("LOGFLAG", False)

llm_component_name = os.getenv("FAQGen_COMPONENT_NAME", "OPEAFAQGen_TGI")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(llm_component_name, description=f"OPEA LLM FAQGen Component: {llm_component_name}")


@register_microservice(
    name="opea_service@llm_faqgen",
    service_type=ServiceType.LLM,
    endpoint="/v1/faqgen",
    host="0.0.0.0",
    port=9000,
)
@register_statistics(names=["opea_service@llm_faqgen"])
async def llm_generate(input: LLMParamsDoc):
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(input)

    try:
        # Use the controller to invoke the active component
        response = await loader.invoke(input)
        # Record statistics
        statistics_dict["opea_service@llm_faqgen"].append_latency(time.time() - start, None)
        return response

    except Exception as e:
        logger.error(f"Error during FaqGen invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA FAQGen Microservice is starting...")
    opea_microservices["opea_service@llm_faqgen"].start()
