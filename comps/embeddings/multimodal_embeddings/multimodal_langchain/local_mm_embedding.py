# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import (
    CustomLogger,
    EmbedDoc,
    EmbedMultimodalDoc,
    MultimodalDoc,
    ServiceType,
    TextDoc,
    TextImageDoc,
    opea_microservices,
    register_microservice,
)
from comps.embeddings.multimodal_embeddings.bridgetower import BridgeTowerEmbedding

logger = CustomLogger("local_multimodal_embedding")
logflag = os.getenv("LOGFLAG", False)

port = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6600))


@register_microservice(
    name="opea_service@local_multimodal_embedding",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=port,
    input_datatype=MultimodalDoc,
    output_datatype=EmbedMultimodalDoc,
)
def embedding(input: MultimodalDoc) -> EmbedDoc:
    if logflag:
        logger.info(input)

    if isinstance(input, TextDoc):
        # Handle text input
        embed_vector = embeddings.embed_query(input.text)
        res = EmbedDoc(text=input.text, embedding=embed_vector)

    elif isinstance(input, TextImageDoc):
        # Handle text + image input
        pil_image = input.image.url.load_pil()
        embed_vector = embeddings.embed_image_text_pairs([input.text.text], [pil_image], batch_size=1)[0]
        res = EmbedMultimodalDoc(text=input.text.text, url=input.image.url, embedding=embed_vector)
    else:
        raise ValueError("Invalid input type")

    if logflag:
        logger.info(res)
    return res


if __name__ == "__main__":
    embeddings = BridgeTowerEmbedding()
    opea_microservices["opea_service@local_multimodal_embedding"].start()
