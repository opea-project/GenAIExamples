#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import contextlib
import os
import time
import urllib.request

import numpy as np
import torch
from datasets import Audio, Dataset
from pydub import AudioSegment
from transformers import WhisperForConditionalGeneration, WhisperProcessor


class AudioSpeechRecognition:
    """Convert audio to text."""

    def __init__(self, model_name_or_path="openai/whisper-small", bf16=False, language="english", device="cpu"):
        if device == "hpu":
            # Explicitly link HPU with Torch
            from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

            adapt_transformers_to_gaudi()

        self.device = device
        asr_model_name_or_path = os.environ.get("ASR_MODEL_PATH", model_name_or_path)
        print("Downloading model: {}".format(asr_model_name_or_path))
        self.model = WhisperForConditionalGeneration.from_pretrained(asr_model_name_or_path).to(self.device)
        self.processor = WhisperProcessor.from_pretrained(asr_model_name_or_path)
        self.model.eval()
        self.bf16 = bf16
        if self.bf16:
            import intel_extension_for_pytorch as ipex

            self.model = ipex.optimize(self.model, dtype=torch.bfloat16)
        self.language = language

        if device == "hpu":
            # do hpu graph warmup with a long enough input audio
            # whisper has a receptive field of 30 seconds
            # here we select a relatively long audio (~15 sec) to quickly warmup
            self._warmup_whisper_hpu_graph("https://paddlespeech.bj.bcebos.com/Parakeet/docs/demos/labixiaoxin.wav")

    def _audiosegment_to_librosawav(self, audiosegment):
        # https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegmentget_array_of_samples
        # This way is faster than librosa.load or HuggingFace Dataset wrapper
        channel_sounds = audiosegment.split_to_mono()[:1]  # only select the first channel
        samples = [s.get_array_of_samples() for s in channel_sounds]

        fp_arr = np.array(samples).T.astype(np.float32)
        fp_arr /= np.iinfo(samples[0].typecode).max
        fp_arr = fp_arr.reshape(-1)

        return fp_arr

    def _warmup_whisper_hpu_graph(self, url):
        print("[ASR] fetch warmup audio...")
        urllib.request.urlretrieve(
            url,
            "warmup.wav",
        )
        print("[ASR] warmup...")
        waveform = AudioSegment.from_file("warmup.wav").set_frame_rate(16000)
        waveform = self._audiosegment_to_librosawav(waveform)
        # pylint: disable=E1101
        inputs = self.processor.feature_extractor(
            waveform, return_tensors="pt", sampling_rate=16_000
        ).input_features.to(self.device)
        _ = self.model.generate(inputs, language="chinese")

    def audio2text(self, audio_path):
        """Convert audio to text.

        audio_path: the path to the input audio, e.g. ~/xxx.mp3
        """
        start = time.time()

        try:
            waveform = AudioSegment.from_file(audio_path).set_frame_rate(16000)
            waveform = self._audiosegment_to_librosawav(waveform)
        except Exception as e:
            print(f"[ASR] audiosegment to librosa wave fail: {e}")
            audio_dataset = Dataset.from_dict({"audio": [audio_path]}).cast_column("audio", Audio(sampling_rate=16000))
            waveform = audio_dataset[0]["audio"]["array"]

        # pylint: disable=E1101
        inputs = self.processor.feature_extractor(
            waveform, return_tensors="pt", sampling_rate=16_000
        ).input_features.to(self.device)
        with torch.cpu.amp.autocast() if self.bf16 else contextlib.nullcontext():
            predicted_ids = self.model.generate(inputs, language=self.language)
        # pylint: disable=E1101
        result = self.processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True, normalize=True)[0]
        if self.language in ["chinese", "mandarin"]:
            from zhconv import convert

            result = convert(result, "zh-cn")
        print(f"generated text in {time.time() - start} seconds, and the result is: {result}")
        return result


if __name__ == "__main__":
    asr = AudioSpeechRecognition(language="english")

    # Test multilanguage asr
    urllib.request.urlretrieve(
        "https://paddlespeech.bj.bcebos.com/Parakeet/docs/demos/labixiaoxin.wav",
        "sample.wav",
    )
    asr.language = "chinese"
    text = asr.audio2text("sample.wav")

    urllib.request.urlretrieve(
        "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav",
        "sample.wav",
    )
    text = asr.audio2text("sample.wav")

    os.remove("sample.wav")
