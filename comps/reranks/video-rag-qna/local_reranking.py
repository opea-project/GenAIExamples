# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import time

from comps import (
    LVMVideoDoc,
    SearchedMultimodalDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

chunk_duration = os.getenv("CHUNK_DURATION", "10") or "10"
chunk_duration = float(chunk_duration) if chunk_duration.isdigit() else 10.0

file_server_endpoint = os.getenv("FILE_SERVER_ENDPOINT") or "http://0.0.0.0:6005"

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s:     [%(asctime)s] %(message)s", datefmt="%d/%m/%Y %I:%M:%S"
)


def get_top_doc(top_n, videos) -> list:
    hit_score = {}
    if videos is None:
        return None
    for video_name in videos:
        try:
            if video_name not in hit_score.keys():
                hit_score[video_name] = 0
            hit_score[video_name] += 1
        except KeyError as r:
            logging.info(f"no video name {r}")

    x = dict(sorted(hit_score.items(), key=lambda item: -item[1]))  # sorted dict of video name and score
    top_n_names = list(x.keys())[:top_n]
    logging.info(f"top docs = {x}")
    logging.info(f"top n docs names = {top_n_names}")

    return top_n_names


def find_timestamp_from_video(metadata_list, video):
    return next(
        (metadata["timestamp"] for metadata in metadata_list if metadata["video"] == video),
        None,
    )


@register_microservice(
    name="opea_service@reranking_visual_rag",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedMultimodalDoc,
    output_datatype=LVMVideoDoc,
)
@register_statistics(names=["opea_service@reranking_visual_rag"])
def reranking(input: SearchedMultimodalDoc) -> LVMVideoDoc:
    start = time.time()

    # get top video name from metadata
    video_names = [meta["video"] for meta in input.metadata]
    top_video_names = get_top_doc(input.top_n, video_names)

    # only use the first top video
    timestamp = find_timestamp_from_video(input.metadata, top_video_names[0])
    video_url = f"{file_server_endpoint.rstrip('/')}/{top_video_names[0]}"

    result = LVMVideoDoc(
        video_url=video_url,
        prompt=input.initial_query,
        chunk_start=timestamp,
        chunk_duration=float(chunk_duration),
        max_new_tokens=512,
    )
    statistics_dict["opea_service@reranking_visual_rag"].append_latency(time.time() - start, None)

    return result


if __name__ == "__main__":
    opea_microservices["opea_service@reranking_visual_rag"].start()
