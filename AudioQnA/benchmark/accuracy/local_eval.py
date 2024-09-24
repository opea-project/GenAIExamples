# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import torch
from datasets import load_dataset
from evaluate import load
from transformers import WhisperForConditionalGeneration, WhisperProcessor

device = "cuda" if torch.cuda.is_available() else "cpu"

MODEL_NAME = "openai/whisper-large-v2"

librispeech_test_clean = load_dataset(
    "andreagasparini/librispeech_test_only", "clean", split="test", trust_remote_code=True
)
processor = WhisperProcessor.from_pretrained(MODEL_NAME)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)


def map_to_pred(batch):
    audio = batch["audio"]
    input_features = processor(audio["array"], sampling_rate=audio["sampling_rate"], return_tensors="pt").input_features
    batch["reference"] = processor.tokenizer._normalize(batch["text"])

    with torch.no_grad():
        predicted_ids = model.generate(input_features.to(device))[0]
    transcription = processor.decode(predicted_ids)
    batch["prediction"] = processor.tokenizer._normalize(transcription)
    return batch


result = librispeech_test_clean.map(map_to_pred)

wer = load("wer")
print(100 * wer.compute(references=result["reference"], predictions=result["prediction"]))
