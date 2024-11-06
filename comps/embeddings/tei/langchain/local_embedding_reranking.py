# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import math
import os
from enum import Enum
from pathlib import Path
from typing import Union

import torch
from habana_frameworks.torch.hpu import wrap_in_hpu_graph
from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi
from sentence_transformers.models import Pooling
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

from comps import (
    CustomLogger,
    EmbedDoc,
    LLMParamsDoc,
    SearchedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
)
from comps.cores.proto.api_protocol import ChatCompletionRequest, EmbeddingRequest, EmbeddingResponse

logger = CustomLogger("local_embedding_reranking")
logflag = os.getenv("LOGFLAG", False)

# keep it consistent for different routers for now
DYNAMIC_BATCHING_TIMEOUT = float(os.getenv("DYNAMIC_BATCHING_TIMEOUT", 0.01))
DYNAMIC_BATCHING_MAX_BATCH_SIZE = int(os.getenv("DYNAMIC_BATCHING_MAX_BATCH_SIZE", 32))
PAD_SEQUENCE_TO_MULTIPLE_OF = int(os.environ.get("PAD_SEQUENCE_TO_MULTIPLE_OF", 128))
EMBEDDING_MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID", "BAAI/bge-base-en-v1.5")
RERANK_MODEL_ID = os.environ.get("RERANK_MODEL_ID", "BAAI/bge-reranker-base")


def round_up(number, k):
    return (number + k - 1) // k * k


class EmbeddingModel:
    def __init__(
        self,
        model_path: Path,
        device: torch.device,
        dtype: torch.dtype,
        trust_remote: bool = False,
    ):
        if device == torch.device("hpu"):
            adapt_transformers_to_gaudi()
        model = AutoModel.from_pretrained(model_path, trust_remote_code=trust_remote).to(dtype).to(device)
        if device == torch.device("hpu"):
            logger.info("Use graph mode for HPU")
            model = wrap_in_hpu_graph(model, disable_tensor_cache=True)
        self.hidden_size = model.config.hidden_size
        self.pooling = Pooling(self.hidden_size, pooling_mode="cls")
        self.model = model

    def embed(self, batch):
        output = self.model(**batch)
        # sentence_embeddings = output[0][:, 0]
        # sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        pooling_features = {
            "token_embeddings": output[0],
            "attention_mask": batch.attention_mask,
        }
        embedding = self.pooling.forward(pooling_features)["sentence_embedding"]
        ## normalize
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        cpu_results = embedding.reshape(-1).tolist()
        return [cpu_results[i * self.hidden_size : (i + 1) * self.hidden_size] for i in range(len(batch.input_ids))]


class RerankingModel:
    def __init__(self, model_path: Path, device: torch.device, dtype: torch.dtype):
        if device == torch.device("hpu"):
            adapt_transformers_to_gaudi()

        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        model = model.to(dtype).to(device)

        if device == torch.device("hpu"):
            logger.info("Use graph mode for HPU")
            model = wrap_in_hpu_graph(model, disable_tensor_cache=True)
        self.model = model

    def predict(self, batch):
        scores = (
            self.model(**batch, return_dict=True)
            .logits.view(
                -1,
            )
            .float()
        )
        scores = torch.sigmoid(scores)
        return scores


def pad_batch(inputs: dict, max_input_len: int):
    # pad seq_len to MULTIPLE OF, pad bs
    batch_size, concrete_length = inputs["input_ids"].size()[0], inputs["input_ids"].size()[1]
    max_length = round_up(concrete_length, PAD_SEQUENCE_TO_MULTIPLE_OF)
    max_length = min(max_length, max_input_len)  # should not exceed max input len
    new_bs = 2 ** math.ceil(math.log2(batch_size))
    for x in inputs:
        inputs[x] = torch.nn.functional.pad(
            inputs[x], (0, max_length - concrete_length, 0, new_bs - batch_size), value=0
        )
    return inputs


async def dynamic_batching_infer(service_type: Enum, batch: list[dict]):
    if logflag:
        logger.info(f"{service_type} {len(batch)} request inference begin >>>")

    if service_type == ServiceType.EMBEDDING:
        sentences = [req["request"].text for req in batch]

        with torch.no_grad():
            encoded_input = embedding_tokenizer(
                sentences,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(device="hpu")
            encoded_input = pad_batch(encoded_input, embedding_tokenizer.model_max_length)
            # with torch.autocast("hpu", dtype=torch.bfloat16):
            results = embedding_model.embed(encoded_input)

        return [EmbedDoc(text=txt, embedding=embed_vector) for txt, embed_vector in zip(sentences, results)]
    elif service_type == ServiceType.RERANK:
        pairs = []
        doc_lengths = []
        for req in batch:
            doc_len = len(req["request"].retrieved_docs)
            doc_lengths.append(doc_len)
            for idx in range(doc_len):
                pairs.append([req["request"].initial_query, req["request"].retrieved_docs[idx].text])

        with torch.no_grad():
            inputs = reranking_tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to("hpu")
            inputs = pad_batch(inputs, reranking_tokenizer.model_max_length)
            scores = reranking_model.predict(inputs)

        # reduce each query's best related doc
        final_results = []
        start = 0
        for idx, doc_len in enumerate(doc_lengths):
            req_scores = scores[start : start + doc_len]
            cur_req = batch[idx]["request"]
            docs: list[TextDoc] = cur_req.retrieved_docs[0:doc_len]
            docs = [doc.text for doc in docs]
            # sort and select top n docs
            top_n_docs = sorted(list(zip(docs, req_scores)), key=lambda x: x[1], reverse=True)[: cur_req.top_n]
            top_n_docs: list[str] = [tupl[0] for tupl in top_n_docs]
            final_results.append(LLMParamsDoc(query=cur_req.initial_query, documents=top_n_docs))

            start += doc_len

        return final_results


@register_microservice(
    name="opea_service@local_embedding_reranking",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6001,
    dynamic_batching=True,
    dynamic_batching_timeout=DYNAMIC_BATCHING_TIMEOUT,
    dynamic_batching_max_batch_size=DYNAMIC_BATCHING_MAX_BATCH_SIZE,
)
async def embedding(
    input: Union[TextDoc, EmbeddingRequest, ChatCompletionRequest]
) -> Union[EmbedDoc, EmbeddingResponse, ChatCompletionRequest]:

    # if logflag:
    #     logger.info(input)
    # Create a future for this specific request
    response_future = asyncio.get_event_loop().create_future()

    cur_microservice = opea_microservices["opea_service@local_embedding_reranking"]
    cur_microservice.dynamic_batching_infer = dynamic_batching_infer
    async with cur_microservice.buffer_lock:
        cur_microservice.request_buffer[ServiceType.EMBEDDING].append({"request": input, "response": response_future})

    # Wait for batch inference to complete and return results
    result = await response_future

    return result


@register_microservice(
    name="opea_service@local_embedding_reranking",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=6001,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
    dynamic_batching=True,
    dynamic_batching_timeout=DYNAMIC_BATCHING_TIMEOUT,
    dynamic_batching_max_batch_size=DYNAMIC_BATCHING_MAX_BATCH_SIZE,
)
async def reranking(input: SearchedDoc) -> LLMParamsDoc:

    # if logflag:
    #     logger.info(input)

    if len(input.retrieved_docs) == 0:
        return LLMParamsDoc(query=input.initial_query)

    # Create a future for this specific request
    response_future = asyncio.get_event_loop().create_future()

    cur_microservice = opea_microservices["opea_service@local_embedding_reranking"]
    cur_microservice.dynamic_batching_infer = dynamic_batching_infer
    async with cur_microservice.buffer_lock:
        cur_microservice.request_buffer[ServiceType.RERANK].append({"request": input, "response": response_future})

    # Wait for batch inference to complete and return results
    result = await response_future

    return result


if __name__ == "__main__":
    embedding_model = EmbeddingModel(model_path=EMBEDDING_MODEL_ID, device=torch.device("hpu"), dtype=torch.bfloat16)
    embedding_tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_ID)
    # sentences = ["sample-1", "sample-2"]
    # encoded_input = embedding_tokenizer(sentences, padding=True, truncation=True, return_tensors='pt').to(device="hpu")
    # results = embedding_model.embed(encoded_input)
    # print(results)
    reranking_model = RerankingModel(model_path=RERANK_MODEL_ID, device=torch.device("hpu"), dtype=torch.bfloat16)
    reranking_tokenizer = AutoTokenizer.from_pretrained(RERANK_MODEL_ID)

    # pairs = [['what is panda?', 'hi'], ['what is panda?', 'The giant panda (Ailuropoda melanoleuca), sometimes called a panda bear or simply panda, is a bear species endemic to China.']]
    # with torch.no_grad():
    #     inputs = reranking_tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512).to("hpu")
    #     scores = reranking_model.predict(inputs)
    #     print(scores)
    opea_microservices["opea_service@local_embedding_reranking"].start(in_single_process=True)
