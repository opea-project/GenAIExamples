# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from os import environ
from typing import Any, Dict, List, Optional, Union

import intel_extension_for_pytorch as ipex
import numpy as np
import torch
from mosec import Server, Worker
from mosec.mixin import TypedMsgPackMixin
from msgspec import Struct
from sentence_transformers import CrossEncoder
from torch.utils.data import DataLoader
from tqdm.autonotebook import tqdm, trange

DEFAULT_MODEL = "/root/bge-reranker-large"


class MyCrossEncoder(CrossEncoder):
    def __init__(
        self,
        model_name: str,
        num_labels: int = None,
        max_length: int = None,
        device: str = None,
        tokenizer_args: Dict = None,
        automodel_args: Dict = None,
        trust_remote_code: bool = False,
        revision: Optional[str] = None,
        local_files_only: bool = False,
        default_activation_function=None,
        classifier_dropout: float = None,
    ) -> None:
        super().__init__(
            model_name,
            num_labels,
            max_length,
            device,
            tokenizer_args,
            automodel_args,
            trust_remote_code,
            revision,
            local_files_only,
            default_activation_function,
            classifier_dropout,
        )
        # jit trace model
        self.model = ipex.optimize(self.model, dtype=torch.float32)
        vocab_size = self.model.config.vocab_size
        batch_size = 16
        seq_length = 512
        d = torch.randint(vocab_size, size=[batch_size, seq_length])
        # t = torch.randint(0, 1, size=[batch_size, seq_length])
        m = torch.randint(1, 2, size=[batch_size, seq_length])
        self.model = torch.jit.trace(self.model, [d, m], check_trace=False, strict=False)
        self.model = torch.jit.freeze(self.model)

    def predict(
        self,
        sentences: List[List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = None,
        num_workers: int = 0,
        activation_fct=None,
        apply_softmax=False,
        convert_to_numpy: bool = True,
        convert_to_tensor: bool = False,
    ) -> Union[List[float], np.ndarray, torch.Tensor]:
        input_was_string = False
        if isinstance(sentences[0], str):  # Cast an individual sentence to a list with length 1
            sentences = [sentences]
            input_was_string = True

        inp_dataloader = DataLoader(
            sentences,
            batch_size=batch_size,
            collate_fn=self.smart_batching_collate_text_only,
            num_workers=num_workers,
            shuffle=False,
        )

        iterator = inp_dataloader
        if show_progress_bar:
            iterator = tqdm(inp_dataloader, desc="Batches")

        if activation_fct is None:
            activation_fct = self.default_activation_function

        pred_scores = []
        self.model.eval()
        self.model.to(self._target_device)
        with torch.no_grad():
            for features in iterator:
                model_predictions = self.model(**features)
                logits = activation_fct(model_predictions["logits"])

                if apply_softmax and len(logits[0]) > 1:
                    logits = torch.nn.functional.softmax(logits, dim=1)
                pred_scores.extend(logits)

        if self.config.num_labels == 1:
            pred_scores = [score[0] for score in pred_scores]

        if convert_to_tensor:
            pred_scores = torch.stack(pred_scores)
        elif convert_to_numpy:
            pred_scores = np.asarray([score.cpu().detach().numpy() for score in pred_scores])

        if input_was_string:
            pred_scores = pred_scores[0]

        return pred_scores


class Request(Struct, kw_only=True):
    query: str
    docs: List[str]


class Response(Struct, kw_only=True):
    scores: List[float]


def float_handler(o):
    if isinstance(o, float):
        return format(o, ".10f")
    raise TypeError("Not serializable")


class MosecReranker(Worker):
    def __init__(self):
        self.model_name = environ.get("MODEL_NAME", DEFAULT_MODEL)
        self.model = MyCrossEncoder(self.model_name)

    def serialize(self, data: Response) -> bytes:
        sorted_list = sorted(data.scores, reverse=True)
        index_sorted = [data.scores.index(i) for i in sorted_list]
        res = []
        for i, s in zip(index_sorted, sorted_list):
            tmp = {"index": i, "score": "{:.10f}".format(s)}
            res.append(tmp)
        return json.dumps(res, default=float_handler).encode("utf-8")

    def forward(self, data: List[Request]) -> List[Response]:
        sentence_pairs = []
        inputs_lens = []
        for d in data:
            inputs_lens.append(len(d["texts"]))
            tmp = [[d["query"], doc] for doc in d["texts"]]
            sentence_pairs.extend(tmp)

        scores = self.model.predict(sentence_pairs)
        scores = scores.tolist()

        resp = []
        cur_idx = 0
        for lens in inputs_lens:
            resp.append(Response(scores=scores[cur_idx : cur_idx + lens]))
            cur_idx += lens

        return resp


if __name__ == "__main__":
    MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", 128))
    MAX_WAIT_TIME = int(os.environ.get("MAX_WAIT_TIME", 10))
    server = Server()
    server.append_worker(MosecReranker, max_batch_size=MAX_BATCH_SIZE, max_wait_time=MAX_WAIT_TIME)
    server.run()
