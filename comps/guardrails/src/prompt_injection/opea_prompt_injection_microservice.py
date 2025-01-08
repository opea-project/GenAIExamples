# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.predictionguard import OpeaPromptInjectionPredictionGuard

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    ScoreDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_prompt_injection_microservice")
logflag = os.getenv("LOGFLAG", False)

prompt_injection_component_name = os.getenv("PROMPT_INJECTION_COMPONENT_NAME", "PREDICTIONGUARD_PROMPT_INJECTION")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    prompt_injection_component_name,
    name=prompt_injection_component_name,
    description=f"OPEA Prompt Injection Component: {prompt_injection_component_name}",
)


@register_microservice(
    name="opea_service@prompt_injection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/injection",
    host="0.0.0.0",
    port=9085,
    input_datatype=TextDoc,
    output_datatype=ScoreDoc,
)
@register_statistics(names=["opea_service@prompt_injection"])
async def injection_guard(input: TextDoc) -> ScoreDoc:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        injection_response = await loader.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {injection_response}")

        # Record statistics
        statistics_dict["opea_service@prompt_injection"].append_latency(time.time() - start, None)
        return injection_response

    except Exception as e:
        logger.error(f"Error during prompt injection invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@prompt_injection"].start()
    logger.info("OPEA Prompt Injection Microservice is up and running successfully...")
