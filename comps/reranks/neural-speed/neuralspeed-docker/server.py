# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Any, List

import numpy
from mosec import Server, Worker, get_logger
from mosec.mixin import TypedMsgPackMixin
from msgspec import Struct
from neural_speed import Model
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = get_logger()

INFERENCE_BATCH_SIZE = 128
INFERENCE_MAX_WAIT_TIME = 10
INFERENCE_WORKER_NUM = 1
INFERENCE_CONTEXT = 512

TorchModel = "/root/bge-reranker-large"
NS_Bin = "/root/bge-large-r-q8.bin"

NS_Model = "bert"


class Request(Struct, kw_only=True):
    query: str
    docs: List[str]


class Response(Struct, kw_only=True):
    scores: List[float]


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
        ndoc = []
        inps = []
        for data in data:
            inp = [[data.query, doc] for doc in data.docs]
            inps.extend(inp)
            ndoc.append(len(data.docs))
        outs = []
        for i in range(0, len(inps), INFERENCE_BATCH_SIZE):
            inp_bs = inps[i : i + INFERENCE_BATCH_SIZE]
            inputs = self.tokenizer(
                inp_bs, padding=True, truncation=True, max_length=INFERENCE_CONTEXT, return_tensors="pt"
            )
            st = time.time()
            output = self.model(
                **inputs,
                reinit=True,
                logits_all=True,
                continuous_batching=False,
                ignore_padding=True,
            )
            logger.info(f"Toal batch {batch} input shape {inputs.input_ids.shape} time {time.time()-st}")
            outs.append(output)
        ns_outputs = numpy.concatenate(outs, axis=0)
        resps = []
        pos = 0
        for i in range(batch):
            resp = Response(scores=ns_outputs[pos : pos + ndoc[i]].tolist())
            pos += ndoc[i]
            resps.append(resp)
        return resps


if __name__ == "__main__":
    INFERENCE_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", 128))
    INFERENCE_MAX_WAIT_TIME = int(os.environ.get("MAX_WAIT_TIME", 1))
    server = Server()
    server.append_worker(
        Inference, max_batch_size=INFERENCE_BATCH_SIZE, max_wait_time=INFERENCE_MAX_WAIT_TIME, num=INFERENCE_WORKER_NUM
    )
    server.run()
