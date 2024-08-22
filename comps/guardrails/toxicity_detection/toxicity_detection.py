# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from transformers import pipeline

from comps import ServiceType, TextDoc, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@toxicity_detection",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/toxicity",
    host="0.0.0.0",
    port=9091,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
def llm_generate(input: TextDoc):
    input_text = input.text
    toxic = toxicity_pipeline(input_text)
    print("done")
    if toxic[0]["label"] == "toxic":
        return TextDoc(text="Violated policies: toxicity, please check your input.", downstream_black_list=[".*"])
    else:
        return TextDoc(text=input_text)


if __name__ == "__main__":
    model = "citizenlab/distilbert-base-multilingual-cased-toxicity"
    toxicity_pipeline = pipeline("text-classification", model=model, tokenizer=model)
    opea_microservices["opea_service@toxicity_detection"].start()
