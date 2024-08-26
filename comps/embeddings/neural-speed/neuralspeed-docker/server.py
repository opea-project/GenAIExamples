# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from typing import Any, List

import numpy
from mosec import Server, Worker, get_logger
from mosec.mixin import TypedMsgPackMixin
from msgspec import Struct
from neural_speed import Model
from transformers import AutoTokenizer

logger = get_logger()

INFERENCE_BATCH_SIZE = 32
INFERENCE_MAX_WAIT_TIME = 30
INFERENCE_WORKER_NUM = 1
INFERENCE_CONTEXT = 512

TorchModel = "/root/bge-base-en-v1.5"
NS_Bin = "/root/bge-base-q8.bin"

NS_Model = "bert"


class Request(Struct, kw_only=True):
    query: str


class Response(Struct, kw_only=True):
    embeddings: List[float]


class Inference(TypedMsgPackMixin, Worker):

    def __init__(self):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(TorchModel)
        self.model = Model()
        self.model.init_from_bin(
            NS_Model,
            NS_Bin,
            batch_size=INFERENCE_BATCH_SIZE,
            n_ctx=INFERENCE_CONTEXT + 2,
        )

    def forward(self, data: List[Request]) -> List[Response]:
        batch = len(data)
        sequences = [d.query for d in data]
        inputs = self.tokenizer(
            sequences,
            padding=True,
            truncation=True,
            max_length=INFERENCE_CONTEXT,
            return_tensors="pt",
        )
        st = time.time()
        ns_outputs = self.model(
            **inputs,
            reinit=True,
            logits_all=True,
            continuous_batching=False,
            ignore_padding=True,
        )
        logger.info(f"batch {batch} input shape {inputs.input_ids.shape} time {time.time()-st}")
        ns_outputs = ns_outputs[:, 0]
        ns_outputs = ns_outputs / numpy.linalg.norm(ns_outputs, axis=1, keepdims=True)
        resps = []
        for i in range(batch):
            resp = Response(embeddings=ns_outputs[i].tolist())
            resps.append(resp)
        return resps


if __name__ == "__main__":
    server = Server()
    server.append_worker(
        Inference, max_batch_size=INFERENCE_BATCH_SIZE, max_wait_time=INFERENCE_MAX_WAIT_TIME, num=INFERENCE_WORKER_NUM
    )
    server.run()
