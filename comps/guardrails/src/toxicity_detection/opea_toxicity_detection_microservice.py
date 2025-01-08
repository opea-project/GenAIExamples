# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.predictionguard import OpeaToxicityDetectionPredictionGuard

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

logger = CustomLogger("opea_toxicity_detection_microservice")
logflag = os.getenv("LOGFLAG", False)

toxicity_detection_component_name = os.getenv("TOXICITY_DETECTION_COMPONENT_NAME", "PREDICTIONGUARD_TOXICITY_DETECTION")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    toxicity_detection_component_name,
    name=toxicity_detection_component_name,
    description=f"OPEA Toxicity Detection Component: {toxicity_detection_component_name}",
)


@register_microservice(
    name="opea_service@toxicity_detection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/toxicity",
    host="0.0.0.0",
    port=9090,
    input_datatype=TextDoc,
    output_datatype=ScoreDoc,
)
@register_statistics(names=["opea_service@toxicity_detection"])
async def toxicity_guard(input: TextDoc) -> ScoreDoc:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        toxicity_response = await loader.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {toxicity_response}")

        # Record statistics
        statistics_dict["opea_service@toxicity_detection"].append_latency(time.time() - start, None)
        return toxicity_response

    except Exception as e:
        logger.error(f"Error during toxicity detection invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@toxicity_detection"].start()
    logger.info("OPEA Toxicity Detection Microservice is up and running successfully...")
