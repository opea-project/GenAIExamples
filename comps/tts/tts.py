# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time

import requests

from comps import (
    Base64ByteStrDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@tts",
    service_type=ServiceType.TTS,
    endpoint="/v1/audio/speech",
    host="0.0.0.0",
    port=9088,
    input_datatype=TextDoc,
    output_datatype=Base64ByteStrDoc,
)
@register_statistics(names=["opea_service@tts"])
async def text_to_audio(input: TextDoc):
    start = time.time()
    text = input.text
    inputs = {"text": text}

    response = requests.post(url=f"{tts_endpoint}/v1/tts", data=json.dumps(inputs), proxies={"http": None})
    statistics_dict["opea_service@tts"].append_latency(time.time() - start, None)
    return Base64ByteStrDoc(byte_str=response.json()["tts_result"])


if __name__ == "__main__":
    tts_endpoint = os.getenv("TTS_ENDPOINT", "http://localhost:7055")
    print("[tts - router] TTS initialized.")
    opea_microservices["opea_service@tts"].start()
