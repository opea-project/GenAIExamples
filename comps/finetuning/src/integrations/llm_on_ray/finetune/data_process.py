# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 The LLM-on-Ray Authors.

import copy
import math
import random
import re
from dataclasses import dataclass
from itertools import chain
from typing import Dict, List, Tuple

import torch
from torch.utils.data import Dataset
from transformers import BatchEncoding, DataCollatorWithPadding

IGNORE_INDEX = -100


class InstructionDataProcessor:
    # We used the following prompts for fine-tuning the Alpaca model. You can find reference doc form this URL(https://github.com/tatsu-lab/stanford_alpaca/blob/main/README.md#data-release)
    def __init__(self, config, tokenizer):
        self.tokenizer = tokenizer
        self.end = tokenizer.eos_token
        self.intro = (
            "Below is an instruction that describes a task. Write a response that appropriately completes the request."
        )
        self.instruction = "### Instruction:\n"
        self.input = "### Input:\n"
        self.response = "### Response:\n"
        self.padding_side = config["Dataset"].get("padding_side", "right")
        self.truncation_side = config["Dataset"].get("truncation_side", "right")
        self.max_length = self.max_seq_length = config["Dataset"].get("max_length", 512)
        self.max_source_length = config["Dataset"].get("max_source_length", 384)
        self.truncation = config["Dataset"].get("truncation", True)
        self.padding = config["Dataset"].get("padding", True)
        self.mask_input = config["Dataset"].get("mask_input", True)
        self.mask_response = config["Dataset"].get("mask_response", True)

    def make_prompt(self, examples):
        prompts = {}
        prompts["prompt_sources"] = []
        prompts["prompt_targets"] = []
        for rec in examples:
            instruction = rec["instruction"]
            response = rec["input"]
            context = rec.get("output")
            if not instruction:
                raise ValueError(f"Expected an instruction in: {rec}")
            # if not response:
            #     raise ValueError(f"Expected a response in: {rec}")
            if context:
                prompt = (
                    self.intro
                    + self.end
                    + "\n"
                    + self.instruction
                    + instruction
                    + self.input
                    + context
                    + self.end
                    + "\n"
                    + self.response
                )
                prompts["prompt_sources"].append(prompt)
            else:
                prompt = self.intro + self.end + "\n" + self.instruction + instruction + self.end + "\n" + self.response
                prompts["prompt_sources"].append(prompt)
            prompt_response = response + self.end
            prompts["prompt_targets"].append(prompt_response)
        return prompts

    def __truncate_sequences(self, sequences, max_length):
        """
        Copied from https://github.com/intel/intel-extension-for-transformers/blob/ae54f698b73a66e5729427cb19f69c33e1a5c34d/intel_extension_for_transformers/transformers/llm/finetuning/data_utils.py#L40
        """
        words_to_cut = sum(list(map(len, sequences))) - max_length
        if words_to_cut <= 0:
            return sequences

        while words_to_cut > 0 and len(sequences) > 0:
            words_to_cut -= len(sequences[0])
            sequences = sequences[1:]
        return sequences

    def tokenize_by_neural_chat(self, examples):
        """
        Copied from https://github.com/intel/intel-extension-for-transformers/blob/ae54f698b73a66e5729427cb19f69c33e1a5c34d/intel_extension_for_transformers/transformers/llm/finetuning/data_utils.py#L225
        The only differences are:
        - using our own prompt style
        - add left or right padding and truncation
        - add mask_input and mask_response
        """
        keys = list(examples.data.keys())
        if len(keys) != 2:
            raise ValueError("Unsupported dataset format")
        assistant_tokens = self.tokenizer.tokenize(self.response)
        header = self.intro + self.end + "\n"

        examples["input_ids"] = []
        examples["labels"] = []
        examples["attention_mask"] = []
        for instruction, response in zip(examples[keys[0]], examples[keys[1]]):
            convs = re.findall(
                r"{0}.*?{2}|{1}.*?{2}".format(self.instruction, self.response, self.end),
                instruction,
                re.DOTALL,
            )
            convs_tokens = [self.tokenizer.tokenize(conv) + self.tokenizer.tokenize("\n") for conv in convs]
            header_tokens = self.tokenizer.tokenize(header) + self.tokenizer.tokenize("\n")
            max_input = self.max_source_length - len(header_tokens) - len(assistant_tokens)
            truncated_convs = self.__truncate_sequences(convs_tokens, max_input)
            if len(truncated_convs) == 0:
                truncated_convs = [convs_tokens[-1][: max_input - 3] + convs_tokens[-1][-3:]]

            prompt_tokens = [header_tokens] + truncated_convs + [assistant_tokens]
            prompt_ids = [self.tokenizer.convert_tokens_to_ids(prompt_token) for prompt_token in prompt_tokens]
            prompt_ids = list(chain(*prompt_ids))

            resp_ids = self.tokenizer.convert_tokens_to_ids(self.tokenizer.tokenize(response.strip()))
            # keep last and eos_id
            max_resp = self.max_seq_length - len(prompt_ids) - 1

            # truncating response
            if len(resp_ids) > max_resp:
                if self.truncation_side == "right":
                    resp_ids = resp_ids[: max_resp - 1] + resp_ids[-1:]
                else:
                    resp_ids = resp_ids[-max_resp:]

            # masking
            input_ids = prompt_ids + resp_ids + [self.tokenizer.eos_token_id]
            if self.mask_input:
                labels = [IGNORE_INDEX] * len(prompt_ids) + resp_ids + [self.tokenizer.eos_token_id]
            elif self.mask_response:
                labels = prompt_ids + [IGNORE_INDEX] * len(resp_ids) + [self.tokenizer.eos_token_id]
            else:
                labels = input_ids

            # padding
            input_len = len(input_ids)
            pad_len = self.max_seq_length - input_len
            if self.padding_side == "right":
                input_ids = input_ids + [self.tokenizer.eos_token_id] * pad_len
                labels = labels + [IGNORE_INDEX] * pad_len
                attention_mask = [1] * input_len + [0] * pad_len
            else:
                input_ids = [self.tokenizer.eos_token_id] * pad_len + input_ids
                labels = [IGNORE_INDEX] * pad_len + labels
                attention_mask = [0] * pad_len + [1] * input_len

            assert len(input_ids) == self.max_seq_length
            assert len(prompt_ids) <= self.max_source_length
            assert len(labels) == len(input_ids) == len(attention_mask)

            examples["input_ids"].append(torch.tensor(input_ids))
            examples["labels"].append(labels)
            examples["attention_mask"].append(attention_mask)

        return examples

    def tokenize(self, examples):
        keys = list(examples.data.keys())
        if len(keys) != 2:
            raise ValueError("Unsupported dataset format")

        examples["input_ids"] = []
        examples["labels"] = []
        examples["attention_mask"] = []
        for s, t in zip(examples[keys[0]], examples[keys[1]]):
            results = self.tokenizer(
                s + t,
                padding=self.padding,
                truncation=self.truncation,
                return_tensors=None,
                max_length=self.max_length,
            )

            input_ids = results["input_ids"]
            input_len = len(input_ids)
            labels = copy.deepcopy(input_ids)
            if self.mask_input or self.mask_response:
                sources_tokenized = self.tokenizer(
                    s,
                    padding=False,
                    truncation=True,
                    return_tensors=None,
                    max_length=self.max_length,
                )
                input_id_len = len(sources_tokenized["input_ids"])
                # mask input
                if self.mask_input:
                    labels[:input_id_len] = [IGNORE_INDEX] * input_id_len
                # mask response
                if self.mask_response:
                    labels[input_id_len:input_len] = [IGNORE_INDEX] * (input_len - input_id_len)

            examples["input_ids"].append(results["input_ids"])
            examples["labels"].append(labels)
            examples["attention_mask"].append(results["attention_mask"])
        return examples


class PretrainingDataProcessor:
    def __init__(self, config, tokenizer):
        self.tokenizer = tokenizer
        self.max_length = self.max_seq_length = config["Dataset"].get("max_length", 512)
        self.truncation = config["Dataset"].get("truncation", True)
        self.padding = config["Dataset"].get("padding", True)

    def tokenize(self, examples):
        keys = list(examples.data.keys())
        if len(keys) != 1 and "text" not in keys:
            raise ValueError("Unsupported dataset format")

        key = keys[0] if len(keys) == 1 else "text"
        examples["input_ids"] = []
        examples["labels"] = []
        examples["attention_mask"] = []
        for exp in examples[key]:
            results = self.tokenizer(
                exp,
                padding=self.padding,
                truncation=self.truncation,
                return_tensors=None,
                max_length=self.max_length,
            )

            input_ids = results["input_ids"]
            labels = copy.deepcopy(input_ids)
            examples["input_ids"].append(results["input_ids"])
            examples["labels"].append(labels)
            examples["attention_mask"].append(results["attention_mask"])
        return examples


class DPODataProcessor:
    def __init__(self, config, tokenizer):
        self.tokenizer = tokenizer
        self.max_length = config["Dataset"].get("max_length", 1024)
        self.max_prompt_length = config["Dataset"].get("max_prompt_length", 512)
        self.pad_to_max = config["Dataset"].get("pad_to_max", False)

    def tokenize(self, examples):
        prompts = {(system + question).strip() for system, question in zip(examples["system"], examples["question"])}
        chosens = {c.strip() for c in examples["chosen"]}
        rejects = {r.strip() for r in examples["rejected"]}

        examples = {
            "prompt": [],
            "chosen": [],
            "rejected": [],
            "chosen_response_only": [],
            "rejected_response_only": [],
            "chosen_input_ids": [],
            "chosen_attention_mask": [],
            "chosen_labels": [],
            "rejected_input_ids": [],
            "rejected_attention_mask": [],
            "rejected_labels": [],
            "prompt_input_ids": [],
            "prompt_attention_mask": [],
        }

        for prompt, chosen, reject in zip(prompts, chosens, rejects):

            prompt_tokens = self.tokenizer.tokenize(prompt)

            if len(prompt_tokens) > self.max_prompt_length:
                prompt_tokens = prompt_tokens[: self.max_prompt_length]

            prompt_ids = self.tokenizer.convert_tokens_to_ids(prompt_tokens)
            prompt_mask = [1] * len(prompt_ids)

            max_resp = self.max_length - len(prompt_ids)
            chosen_tokens = self.tokenizer.tokenize(chosen)
            chosen_tokens = chosen_tokens[: max_resp - 1]
            chosen_tokens.append(self.tokenizer.eos_token)
            chosen_ids = self.tokenizer.convert_tokens_to_ids(chosen_tokens)
            chosen_mask = [1] * len(chosen_ids)

            reject_tokens = self.tokenizer.tokenize(reject)
            reject_tokens = reject_tokens[: max_resp - 1]
            reject_tokens.append(self.tokenizer.eos_token)
            reject_ids = self.tokenizer.convert_tokens_to_ids(reject_tokens)
            reject_mask = [1] * len(reject_ids)

            chosen_input_ids = prompt_ids + chosen_ids
            chosen_attention_mask = prompt_mask + chosen_mask
            chosen_labels = [IGNORE_INDEX] * len(prompt_ids) + chosen_ids

            reject_input_ids = prompt_ids + reject_ids
            reject_attention_mask = prompt_mask + reject_mask
            reject_labels = [IGNORE_INDEX] * len(prompt_ids) + reject_ids

            # padding
            input_len = len(chosen_input_ids)
            if self.pad_to_max:
                pad_len = self.max_length - input_len
                chosen_input_ids = chosen_input_ids + [0] * pad_len
                chosen_labels = chosen_labels + [-100] * pad_len
                chosen_attention_mask = chosen_attention_mask + [0] * pad_len
                assert len(chosen_input_ids) == self.max_length

            input_len = len(reject_input_ids)
            if self.pad_to_max:
                pad_len = self.max_length - input_len
                reject_input_ids = reject_input_ids + [0] * pad_len
                reject_labels = reject_labels + [-100] * pad_len
                reject_attention_mask = reject_attention_mask + [0] * pad_len
                assert len(reject_input_ids) == self.max_length

            examples["prompt"].append(prompt)
            examples["chosen"].append(prompt + chosen)
            examples["rejected"].append(prompt + reject)
            examples["chosen_response_only"].append(chosen)
            examples["rejected_response_only"].append(reject)

            examples["chosen_input_ids"].append(chosen_input_ids)
            examples["chosen_attention_mask"].append(chosen_attention_mask)
            examples["chosen_labels"].append(chosen_labels)

            examples["rejected_input_ids"].append(reject_input_ids)
            examples["rejected_attention_mask"].append(reject_attention_mask)
            examples["rejected_labels"].append(reject_labels)

            examples["prompt_input_ids"].append(prompt_ids)
            examples["prompt_attention_mask"].append(prompt_mask)

        return examples


class TrainDatasetForCE(Dataset):
    def __init__(self, dataset, args, tokenizer):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.args = args
        self.total_len = len(self.dataset)

    def create_one_example(self, qry_encoding: str, doc_encoding: str):
        item = self.tokenizer.encode_plus(
            qry_encoding,
            doc_encoding,
            truncation=True,
            max_length=self.args.get("max_length", 512),
            padding=False,
        )
        return item

    def __len__(self):
        return self.total_len

    def __getitem__(self, item) -> List[BatchEncoding]:
        query = self.dataset[item]["query"]
        pos = random.choice(self.dataset[item]["pos"])
        train_group_size = self.args.get("train_group_size", 8)
        if len(self.dataset[item]["neg"]) < train_group_size - 1:
            num = math.ceil((train_group_size - 1) / len(self.dataset[item]["neg"]))
            negs = random.sample(self.dataset[item]["neg"] * num, train_group_size - 1)
        else:
            negs = random.sample(self.dataset[item]["neg"], train_group_size - 1)

        batch_data = []
        batch_data.append(self.create_one_example(query, pos))
        for neg in negs:
            batch_data.append(self.create_one_example(query, neg))

        return batch_data


@dataclass
class GroupCollator(DataCollatorWithPadding):
    def __call__(self, features) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
        if isinstance(features[0], list):
            features = sum(features, [])
        return super().__call__(features)


class TrainDatasetForEmbedding(Dataset):
    def __init__(self, dataset, args, tokenizer):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.args = args
        self.total_len = len(self.dataset)

    def __len__(self):
        return self.total_len

    def __getitem__(self, item) -> Tuple[str, List[str]]:
        query = self.dataset[item]["query"]
        if self.args["query_instruction_for_retrieval"] is not None:
            query = self.args["query_instruction_for_retrieval"] + query

        passages = []

        assert isinstance(self.dataset[item]["pos"], list)
        pos = random.choice(self.dataset[item]["pos"])
        passages.append(pos)

        train_group_size = self.args.get("train_group_size", 8)
        if len(self.dataset[item]["neg"]) < train_group_size - 1:
            num = math.ceil((train_group_size - 1) / len(self.dataset[item]["neg"]))
            negs = random.sample(self.dataset[item]["neg"] * num, train_group_size - 1)
        else:
            negs = random.sample(self.dataset[item]["neg"], train_group_size - 1)
        passages.extend(negs)

        if self.args["passage_instruction_for_retrieval"] is not None:
            passages = [self.args["passage_instruction_for_retrieval"] + p for p in passages]
        return query, passages


@dataclass
class EmbedCollator(DataCollatorWithPadding):
    """Wrapper that does conversion from List[Tuple[encode_qry, encode_psg]] to List[qry], List[psg]
    and pass batch separately to the actual collator.

    Abstract out data detail for the model.
    """

    query_max_len: int = 32
    passage_max_len: int = 128

    def __call__(self, features):
        query = [f[0] for f in features]
        passage = [f[1] for f in features]

        if isinstance(query[0], list):
            query = sum(query, [])
        if isinstance(passage[0], list):
            passage = sum(passage, [])

        q_collated = self.tokenizer(
            query,
            padding=self.padding,
            truncation=True,
            max_length=self.query_max_len,
            return_tensors="pt",
        )
        d_collated = self.tokenizer(
            passage,
            padding=self.padding,
            truncation=True,
            max_length=self.passage_max_len,
            return_tensors="pt",
        )
        return {"query": q_collated, "passage": d_collated}


@dataclass
class DPOCollator(DataCollatorWithPadding):
    def __call__(self, features) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
        input_ids = [torch.tensor(ins["chosen_input_ids"]) for ins in features] + [
            torch.tensor(ins["rejected_input_ids"]) for ins in features
        ]
        labels = [torch.tensor(ins["chosen_labels"]) for ins in features] + [
            torch.tensor(ins["rejected_labels"]) for ins in features
        ]
        attention_mask = [torch.tensor(ins["chosen_attention_mask"]) for ins in features] + [
            torch.tensor(ins["rejected_attention_mask"]) for ins in features
        ]

        input_ids = torch.nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=self.tokenizer.eos_token_id
        )
        labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=IGNORE_INDEX)
        attention_mask = torch.nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0)
        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=attention_mask,
        )
