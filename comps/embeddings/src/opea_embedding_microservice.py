# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.opea_tei_embedding import OpeaTEIEmbedding
from integrations.predictionguard_embedding import PredictionguardEmbedding

from comps import (
    CustomLogger,
    OpeaComponentController,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import EmbeddingRequest, EmbeddingResponse

logger = CustomLogger("opea_embedding_microservice")
logflag = os.getenv("LOGFLAG", False)

# Initialize OpeaComponentController
controller = OpeaComponentController()

# Register components
try:
    # Instantiate Embedding components and register it to controller
    if os.getenv("TEI_EMBEDDING_ENDPOINT"):
        opea_tei_embedding = OpeaTEIEmbedding(
            name="OpeaTEIEmbedding",
            description="OPEA TEI Embedding Service",
        )
        controller.register(opea_tei_embedding)
    if os.getenv("PREDICTIONGUARD_API_KEY"):
        predictionguard_embedding = PredictionguardEmbedding(
            name="PredictionGuardEmbedding",
            description="Prediction Guard Embedding Service",
        )
        controller.register(predictionguard_embedding)

    # Discover and activate a healthy component
    controller.discover_and_activate()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")


@register_microservice(
    name="opea_service@embedding",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
)
@register_statistics(names=["opea_service@embedding"])
async def embedding(input: EmbeddingRequest) -> EmbeddingResponse:
    start = time.time()

    # Log the input if logging is enabled
    if logflag:
        logger.info(f"Input received: {input}")

    try:
        # Use the controller to invoke the active component
        embedding_response = await controller.invoke(input)

        # Log the result if logging is enabled
        if logflag:
            logger.info(f"Output received: {embedding_response}")

        # Record statistics
        statistics_dict["opea_service@embedding"].append_latency(time.time() - start, None)
        return embedding_response

    except Exception as e:
        logger.error(f"Error during embedding invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@embedding"].start()
    logger.info("OPEA Embedding Microservice is up and running successfully...")
