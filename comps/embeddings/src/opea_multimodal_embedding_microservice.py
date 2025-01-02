# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from integrations.opea_multimodal_embedding_bridgetower import OpeaMultimodalEmbeddingBrigeTower

from comps import (
    CustomLogger,
    EmbedMultimodalDoc,
    MultimodalDoc,
    OpeaComponentController,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("opea_multimodal_embedding_microservice")
logflag = os.getenv("LOGFLAG", False)

# Initialize OpeaComponentController
controller = OpeaComponentController()

# Register components
try:
    # Instantiate Embedding components and register it to controller
    if os.getenv("MMEI_EMBEDDING_ENDPOINT"):
        opea_mm_embedding_bt = OpeaMultimodalEmbeddingBrigeTower(
            name="OpeaMultimodalEmbeddingBrigeTower",
            description="OPEA Multimodal Embedding Service using BridgeTower",
        )
        controller.register(opea_mm_embedding_bt)

    # Discover and activate a healthy component
    controller.discover_and_activate()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")

port = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6000))


@register_microservice(
    name="opea_service@multimodal_embedding",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=port,
    input_datatype=MultimodalDoc,
    output_datatype=EmbedMultimodalDoc,
)
@register_statistics(names=["opea_service@multimodal_embedding"])
async def embedding(input: MultimodalDoc) -> EmbedMultimodalDoc:
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
        statistics_dict["opea_service@multimodal_embedding"].append_latency(time.time() - start, None)
        return embedding_response

    except Exception as e:
        logger.error(f"Error during embedding invocation: {e}")
        raise


if __name__ == "__main__":
    opea_microservices["opea_service@multimodal_embedding"].start()
    logger.info("OPEA Multimodal Embedding Microservice is up and running successfully...")
