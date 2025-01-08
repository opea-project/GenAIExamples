# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.distilbias import OpeaBiasDetectionNative

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_bias_detection_microservice")
logflag = os.getenv("LOGFLAG", False)

bias_detection_component_name = os.getenv("BIAS_DETECTION_COMPONENT_NAME", "OPEA_NATIVE_BIAS")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    bias_detection_component_name,
    name=bias_detection_component_name,
    description=f"OPEA BIAS Detection Component: {bias_detection_component_name}",
)


@register_microservice(
    name="opea_service@bias_detection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/bias",
    host="0.0.0.0",
    port=9092,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
@register_statistics(names=["opea_service@bias_detection"])
async def llm_generate(input: TextDoc):
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        bias_response = await loader.invoke(input.text)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {bias_response}")

        # Record statistics
        statistics_dict["opea_service@bias_detection"].append_latency(time.time() - start, None)
        return bias_response

    except Exception as e:
        logger.error(f"Error during bias detection invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@bias_detection"].start()
    logger.info("OPEA BIAS Detection Microservice is up and running successfully...")
