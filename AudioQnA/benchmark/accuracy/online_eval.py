# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json

import requests
import torch
from datasets import load_dataset
from evaluate import load
from pydub import AudioSegment
from transformers import WhisperForConditionalGeneration, WhisperProcessor

MODEL_NAME = "openai/whisper-large-v2"
processor = WhisperProcessor.from_pretrained(MODEL_NAME)

librispeech_test_clean = load_dataset(
    "andreagasparini/librispeech_test_only", "clean", split="test", trust_remote_code=True
)


def map_to_pred(batch):
    batch["reference"] = processor.tokenizer._normalize(batch["text"])

    file_path = batch["file"]
    # process the file_path
    pidx = file_path.rfind("/")
    sidx = file_path.rfind(".")

    file_path_prefix = file_path[: pidx + 1]
    file_path_suffix = file_path[sidx:]
    file_path_mid = file_path[pidx + 1 : sidx]
    splits = file_path_mid.split("-")
    file_path_mid = f"LibriSpeech/test-clean/{splits[0]}/{splits[1]}/{file_path_mid}"

    file_path = file_path_prefix + file_path_mid + file_path_suffix

    audio = AudioSegment.from_file(file_path)
    audio.export("tmp.wav")
    with open("tmp.wav", "rb") as f:
        test_audio_base64_str = base64.b64encode(f.read()).decode("utf-8")

    inputs = {"audio": test_audio_base64_str}
    endpoint = "http://localhost:7066/v1/asr"
    response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})

    result_str = response.json()["asr_result"]

    batch["prediction"] = processor.tokenizer._normalize(result_str)
    return batch


result = librispeech_test_clean.map(map_to_pred)

wer = load("wer")
print(100 * wer.compute(references=result["reference"], predictions=result["prediction"]))
