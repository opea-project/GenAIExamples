# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import datetime
import os
import time
from typing import List, Optional, Union

from dateparser.search import search_dates
from embeddings_clip import vCLIP

from comps import (
    CustomLogger,
    EmbedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingResponseData,
)

logger = CustomLogger("embedding_multimodal")
logflag = os.getenv("LOGFLAG", False)


def filtler_dates(prompt):

    base_date = datetime.datetime.today()
    today_date = base_date.date()
    dates_found = search_dates(prompt, settings={"PREFER_DATES_FROM": "past", "RELATIVE_BASE": base_date})

    if dates_found is not None:
        for date_tuple in dates_found:
            date_string, parsed_date = date_tuple
            date_out = str(parsed_date.date())
            time_out = str(parsed_date.time())
            hours, minutes, seconds = map(float, time_out.split(":"))
            year, month, day_out = map(int, date_out.split("-"))

        rounded_seconds = min(round(parsed_date.second + 0.5), 59)
        parsed_date = parsed_date.replace(second=rounded_seconds, microsecond=0)

        iso_date_time = parsed_date.isoformat()
        iso_date_time = str(iso_date_time)

        if date_string == "today":
            constraints = {"date": ["==", date_out]}
        elif date_out != str(today_date) and time_out == "00:00:00":  ## exact day (example last friday)
            constraints = {"date": ["==", date_out]}
        elif (
            date_out == str(today_date) and time_out == "00:00:00"
        ):  ## when search_date interprates words as dates output is todays date + time 00:00:00
            constraints = {}
        else:  ## Interval  of time:last 48 hours, last 2 days,..
            constraints = {"date_time": [">=", {"_date": iso_date_time}]}
        return constraints

    else:
        return {}


@register_microservice(
    name="opea_service@embedding_multimodal",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
@register_statistics(names=["opea_service@embedding_multimodal"])
async def embedding(
    input: Union[TextDoc, EmbeddingRequest, ChatCompletionRequest]
) -> Union[EmbedDoc, EmbeddingResponse, ChatCompletionRequest]:
    if logflag:
        logger.info(input)
    start = time.time()

    if isinstance(input, TextDoc):
        embed_vector = await get_embeddings(input.text)
        if isinstance(input.text, str):
            embedding_res = embed_vector[0]
            constraints_res = filtler_dates(input.text)
        else:
            embedding_res = embed_vector
            constraints_res = [filtler_dates(input.text[i]) for i in range(len(input.text))]
        res = EmbedDoc(text=input.text, embedding=embedding_res, constraints=constraints_res)
    else:
        embed_vector = await get_embeddings(input.input)
        if input.dimensions is not None:
            embed_vector = [embed_vector[i][: input.dimensions] for i in range(len(embed_vector))]

        # for standard openai embedding format
        res = EmbeddingResponse(
            data=[EmbeddingResponseData(index=i, embedding=embed_vector[i]) for i in range(len(embed_vector))]
        )

        if isinstance(input, ChatCompletionRequest):
            input.embedding = res
            # keep
            res = input

    statistics_dict["opea_service@embedding_multimodal"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(res)
    return res


async def get_embeddings(text: Union[str, List[str]]) -> List[List[float]]:
    texts = [text] if isinstance(text, str) else text
    embed_vector = embeddings.embed_query(texts).tolist()
    return embed_vector


if __name__ == "__main__":
    embeddings = vCLIP({"model_name": "openai/clip-vit-base-patch32", "num_frm": 4})
    opea_microservices["opea_service@embedding_multimodal"].start()
