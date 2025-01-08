# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.predictionguard import OpeaFactualityPredictionGuard

from comps import (
    CustomLogger,
    FactualityDoc,
    OpeaComponentLoader,
    ScoreDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_facutality_microservice")
logflag = os.getenv("LOGFLAG", False)

facutality_component_name = os.getenv("FACUTALITY_COMPONENT_NAME", "OPEA_FACTUALITY_PREDICTIONGUARD")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    facutality_component_name,
    name=facutality_component_name,
    description=f"OPEA Facutality Alignment Component: {facutality_component_name}",
)


@register_microservice(
    name="opea_service@factuality_alignment",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/factuality",
    host="0.0.0.0",
    port=9075,
    input_datatype=FactualityDoc,
    output_datatype=ScoreDoc,
)
@register_statistics(names=["opea_service@factuality_alignment"])
async def factuality_guard(input: FactualityDoc) -> ScoreDoc:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the loader to invoke the component
        factuality_response = await loader.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {factuality_response}")

        # Record statistics
        statistics_dict["opea_service@factuality_alignment"].append_latency(time.time() - start, None)
        return factuality_response

    except Exception as e:
        logger.error(f"Error during factuality alignment invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@factuality_alignment"].start()
    logger.info("OPEA Facutality Alignment Microservice is up and running successfully...")
