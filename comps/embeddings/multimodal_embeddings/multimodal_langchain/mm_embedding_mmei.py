# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import os
import time

import requests
from fastapi.responses import JSONResponse

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
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("multimodal_embedding_mmei_langchain")
logflag = os.getenv("LOGFLAG", False)
port = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6600))
headers = {"Content-Type": "application/json"}


@register_microservice(
    name="opea_service@multimodal_embedding_mmei_langchain",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=port,
    input_datatype=MultimodalDoc,
    output_datatype=EmbedMultimodalDoc,
)
@register_statistics(names=["opea_service@multimodal_embedding_mmei_langchain"])
def embedding(input: MultimodalDoc) -> EmbedDoc:
    start = time.time()
    if logflag:
        logger.info(input)

    json = {}
    if isinstance(input, TextDoc):
        json["text"] = input.text
    elif isinstance(input, TextImageDoc):
        json["text"] = input.text.text
        img_bytes = input.image.url.load_bytes()
        base64_img = base64.b64encode(img_bytes).decode("utf-8")
        json["img_b64_str"] = base64_img
    else:
        return JSONResponse(status_code=400, content={"message": "Bad request!"})

    # call multimodal embedding endpoint
    try:
        response = requests.post(mmei_embedding_endpoint, headers=headers, json=json)
        if response.status_code != 200:
            return JSONResponse(status_code=503, content={"message": "Multimodal embedding endpoint failed!"})

        response_json = response.json()
        embed_vector = response_json["embedding"]
        if isinstance(input, TextDoc):
            res = EmbedDoc(text=input.text, embedding=embed_vector)
        elif isinstance(input, TextImageDoc):
            res = EmbedMultimodalDoc(text=input.text.text, url=input.image.url, embedding=embed_vector)
    except requests.exceptions.ConnectionError:
        res = JSONResponse(status_code=503, content={"message": "Multimodal embedding endpoint not started!"})
    statistics_dict["opea_service@multimodal_embedding_mmei_langchain"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(res)
    return res


if __name__ == "__main__":
    url_endpoint = os.getenv("MMEI_EMBEDDING_HOST_ENDPOINT", "http://0.0.0.0")
    port_endpoint = os.getenv("MMEI_EMBEDDING_PORT_ENDPOINT", "8080")
    path_endpoint = os.getenv("MMEI_EMBEDDING_PATH_ENDPOINT", "/v1/encode")

    mmei_embedding_endpoint = os.getenv("MMEI_EMBEDDING_ENDPOINT", f"{url_endpoint}:{port_endpoint}{path_endpoint}")
    logger.info(f"MMEI Gaudi Embedding initialized at {mmei_embedding_endpoint}")
    opea_microservices["opea_service@multimodal_embedding_mmei_langchain"].start()
