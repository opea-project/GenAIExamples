# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.predictionguard import OpeaPiiDetectionPredictionGuard

from comps import (
    CustomLogger,
    OpeaComponentLoader,
    PIIRequestDoc,
    PIIResponseDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_pii_detection_microservice")
logflag = os.getenv("LOGFLAG", False)

pii_detection_component_name = os.getenv("PII_DETECTION_COMPONENT_NAME", "PREDICTIONGUARD_PII_DETECTION")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    pii_detection_component_name,
    name=pii_detection_component_name,
    description=f"OPEA PII Detection Component: {pii_detection_component_name}",
)


@register_microservice(
    name="opea_service@pii_detection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/pii",
    host="0.0.0.0",
    port=9080,
    input_datatype=PIIRequestDoc,
    output_datatype=PIIResponseDoc,
)
@register_statistics(names=["opea_service@pii_detection"])
async def pii_guard(input: PIIRequestDoc) -> PIIResponseDoc:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        pii_response = await loader.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {pii_response}")

        # Record statistics
        statistics_dict["opea_service@pii_detection"].append_latency(time.time() - start, None)
        return pii_response

    except Exception as e:
        logger.error(f"Error during PII detection invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@pii_detection"].start()
    logger.info("OPEA PII Detection Microservice is up and running successfully...")
