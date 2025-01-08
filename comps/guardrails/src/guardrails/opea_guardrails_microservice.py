# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union

from integrations.llamaguard import OpeaGuardrailsLlamaGuard
from integrations.wildguard import OpeaGuardrailsWildGuard

from comps import (
    CustomLogger,
    GeneratedDoc,
    OpeaComponentLoader,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_guardrails_microservice")
logflag = os.getenv("LOGFLAG", False)

guardrails_component_name = os.getenv("GUARDRAILS_COMPONENT_NAME", "OPEA_LLAMA_GUARD")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    guardrails_component_name,
    name=guardrails_component_name,
    description=f"OPEA Guardrails Component: {guardrails_component_name}",
)


@register_microservice(
    name="opea_service@guardrails",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/guardrails",
    host="0.0.0.0",
    port=9090,
    input_datatype=Union[GeneratedDoc, TextDoc],
    output_datatype=TextDoc,
)
@register_statistics(names=["opea_service@guardrails"])
async def safety_guard(input: Union[GeneratedDoc, TextDoc]) -> TextDoc:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        guardrails_response = await loader.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {guardrails_response}")

        # Record statistics
        statistics_dict["opea_service@guardrails"].append_latency(time.time() - start, None)
        return guardrails_response

    except Exception as e:
        logger.error(f"Error during guardrails invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@guardrails"].start()
    logger.info("OPEA guardrails Microservice is up and running successfully...")
