# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
from abc import ABC

import aiohttp
import numpy
from edgecraftrag.config_repository import MilvusConfigRepository
from omegaconf import OmegaConf


class _BaseEstimator(ABC):
    """Base class for LLM-based estimators.

    This class is abstract
    """

    def __init__(
        self,
        model_id,
        device=None,
        generation_config=None,
        instructions="",
        input_template="",
        output_template="",
        temperature=1.0,
        **_,
    ):
        self.instructions = instructions or self._DEFAULT_INSTRUCTIONS_PROMPT
        self.input_template = input_template or self._DEFAULT_INPUT_PROMPT_TEMPLATE
        self.output_template = output_template or self._DEFAULT_OUTPUT_PROMPT_TEMPLATE
        self.temperature = temperature

        self.prefilled_messages = [{"role": "system", "content": self.instructions}]


class LogitsEstimator(_BaseEstimator):
    """A class that uses a LLM to evaluate the relevance of a (query, response) pair.

    Follow BGE interface.
    """

    _DEFAULT_INSTRUCTIONS_PROMPT = "You are an AI assistant. Your mission is to predict the relevance of the following query and response given by the user.\n"
    _DEFAULT_INPUT_PROMPT_TEMPLATE = "Query: {}\nnResponse: {}\n\n"
    _DEFAULT_OUTPUT_PROMPT_TEMPLATE = "Are the above query and response relevant?"

    def __init__(
        self,
        model_id,
        device=None,
        generation_config=None,
        instructions="",
        input_template="",
        output_template="",
        output_levels=["No", "Yes"],
        temperature=1.0,
        **kwargs,
    ):
        super().__init__(
            model_id, device, generation_config, instructions, input_template, output_template, temperature, **kwargs
        )
        self.output_token_ids = []
        self.output_levels = output_levels


class LogitsEstimatorJSON(LogitsEstimator):
    """A class that uses a LLM to evaluate the relevance of a (query, response) pair.

    Follow BGE interface.
    """

    _DEFAULT_INSTRUCTIONS_PROMPT = "You are an AI assistant. Your mission is to predict the relevance of the following query and response given by the user.\n"
    _DEFAULT_INPUT_PROMPT_TEMPLATE = "Query: {}\nnResponse: {}\n\n"
    _DEFAULT_OUTPUT_PROMPT_TEMPLATE = "Now predict if the query and response above are relevant. Format your output as a JSON object with a single key {json_key} and a value from {json_value}."

    def __init__(
        self,
        model_id,
        device=None,
        generation_config=None,
        instructions="",
        input_template="",
        output_template="",
        json_key="relevance",
        json_levels=["Low", "High"],
        scores_weight=None,
        temperature=1.0,
        API_BASE=None,
        **kwargs,
    ):
        """Initialize the LLM-based relevance estimator."""

        super().__init__(
            model_id,
            device,
            generation_config,
            instructions,
            input_template,
            output_template,
            json_levels,
            temperature,
            **kwargs,
        )

        self.json_key = json_key
        self.json_levels = json_levels
        self.API_BASE = API_BASE

        # dynamically set scores_weight, use default if not provided
        if scores_weight is None:
            # generate default weights based on json_levels count
            if len(json_levels) == 2:
                self.scores_weight = [0.0, 1.0]  # Low, High
            elif len(json_levels) == 3:
                self.scores_weight = [0.0, 0.5, 1.0]  # Low, Medium, High
            else:
                # for other counts, generate evenly spaced weights
                self.scores_weight = [i / (len(json_levels) - 1) for i in range(len(json_levels))]
        else:
            self.scores_weight = scores_weight

    async def invoke_vllm(self, input_texts):
        headers = {"Content-Type": "application/json"}
        payload = {
            "prompt": input_texts[0],
            "max_tokens": 1,
            "logprobs": 15,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_BASE, headers=headers, json=payload) as response:
                response.raise_for_status()
                results = await response.json()

        output_texts = results["choices"][0]["text"]
        output_logits = results["choices"][0]["logprobs"]["top_logprobs"][0]

        return output_texts, output_logits

    async def _calculate_logits_score(self, user_input, issue):
        query_and_chunk = self.input_template.format(user_input, issue)
        output_instructions = self.output_template.format(
            json_key=f'"{self.json_key}"',
            json_levels="[{}]".format(", ".join([f'"{jval}"' for jval in self.json_levels])),
        )

        messages = self.prefilled_messages + [
            {"role": "user", "content": query_and_chunk},
            {"role": "system", "content": output_instructions},
        ]
        input_text = ""
        for msg in messages:
            if msg["role"] == "system":
                input_text += "system\n" + msg["content"] + "\n"
            elif msg["role"] == "user":
                input_text += "user\n" + msg["content"] + "\n"
            elif msg["role"] == "assistant":
                input_text += "assistant\n" + msg["content"] + "\n"
        input_text += "assistant\n<think>\n</think>\nanswer:\n"
        outputs = await self.invoke_vllm([input_text])
        score = self._calculate_token_score_vllm(outputs)

        return score

    def _calculate_token_score_vllm(self, outputs, output_index=1, transform="exp"):
        generated_scores = outputs[output_index]

        # dynamically get scores for all levels
        level_scores = []
        for level in self.json_levels:
            level_scores.append(generated_scores.get(level, -9999.0))

        # apply temperature scaling
        level_scores = [score / self.temperature for score in level_scores]

        level_scores_np = numpy.array(level_scores)
        level_scores_np = numpy.where(level_scores_np < -1000, -1000, level_scores_np)
        level_scores_np_exp = numpy.exp(level_scores_np - numpy.max(level_scores_np))
        scores_probs = level_scores_np_exp / level_scores_np_exp.sum()

        # using dynamic scores_weight
        scores_weight = numpy.array(self.scores_weight)
        final_score = numpy.dot(scores_probs, scores_weight)

        return final_score

    async def compute_score(self, input_pair):
        return await self._calculate_logits_score(*input_pair)


experience_repo = MilvusConfigRepository.create_connection("experience_data", 1)


def read_json_files(file_path: str) -> dict:
    experience_lists = []
    if experience_repo:
        experience_lists = []
        for experience in experience_repo.get_configs():
            experience_lists.append(experience["config_json"])
    else:
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                experience_lists = json.load(f)
    return experience_lists


async def query_search(user_input, SEARCH_CONFIG_PATH, SEARCH_DIR, pl):
    top1_issue = None
    sub_questions_result = None

    model_id = pl.generator.model_id
    vllm_endpoint = pl.generator.vllm_endpoint

    maintenance_data = read_json_files(SEARCH_DIR)
    issues = []
    for i in range(len(maintenance_data)):
        issues.append(maintenance_data[i]["question"])
    if not issues:
        return top1_issue, sub_questions_result

    cfg = {}
    if not os.path.exists(SEARCH_CONFIG_PATH):
        cfg["query_matcher"] = {
            "instructions": "You're a knowledgeable assistant. Your task is to judge if two queries ask for the same information about the same primary subject. Output only 'Yes' or 'No'. Yes = same subject entity AND same information need, with only wording or stylistic differences. No = different subject entity, different spec or numeric constraint, different attribute/metric, or scope changed by adding/removing a restricting condition. Entity changes MUST lead to No.",
            "input_template": "Query 1: {}\nQuery 2: {}\n",
            "output_template": "\nAre these queries equivalent? Answer 'Yes' or 'No':",
            "json_key": "similarity",
            "json_levels": ["No", "Yes"],
            "temperature": 0.1,
        }
    else:
        cfg = OmegaConf.load(SEARCH_CONFIG_PATH)
    cfg["query_matcher"]["model_id"] = model_id
    cfg["query_matcher"]["API_BASE"] = os.path.join(vllm_endpoint, "v1/completions")
    query_matcher = LogitsEstimatorJSON(**cfg["query_matcher"])
    semaphore = asyncio.Semaphore(200)

    async def limited_compute_score(query_matcher, user_input, issue):
        async with semaphore:
            return await query_matcher.compute_score((user_input, issue))

    tasks = [limited_compute_score(query_matcher, user_input, issue) for issue in issues]
    scores = await asyncio.gather(*tasks)
    match_scores = list(zip(issues, scores))
    match_scores.sort(key=lambda x: x[1], reverse=True)

    # Maximum less than 0.6, we don't use query search.
    if match_scores[0][1] < 0.6:
        return top1_issue, sub_questions_result
    top1_issue = match_scores[0][0]
    for i in range(len(maintenance_data)):
        if maintenance_data[i]["question"] == top1_issue:
            sub_questions_result = "\n".join(maintenance_data[i]["content"])
    return top1_issue, sub_questions_result
