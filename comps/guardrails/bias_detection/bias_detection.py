# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from transformers import pipeline

from comps import ServiceType, TextDoc, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@bias_detection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/bias",
    host="0.0.0.0",
    port=9092,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
def llm_generate(input: TextDoc):
    input_text = input.text
    toxic = bias_pipeline(input_text)
    print("done")
    if toxic[0]["label"] == "BIASED":
        return TextDoc(text="Violated policies: bias, please check your input.", downstream_black_list=[".*"])
    else:
        return TextDoc(text=input_text)


if __name__ == "__main__":
    model = "valurank/distilroberta-bias"
    bias_pipeline = pipeline("text-classification", model=model, tokenizer=model)
    opea_microservices["opea_service@bias_detection"].start()
