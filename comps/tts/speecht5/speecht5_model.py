# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess

import numpy as np
import torch
from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor


class SpeechT5Model:
    def __init__(self, device="cpu"):
        self.device = device
        if self.device == "hpu":
            from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

            adapt_transformers_to_gaudi()

        model_name_or_path = "microsoft/speecht5_tts"
        vocoder_model_name_or_path = "microsoft/speecht5_hifigan"
        self.model = SpeechT5ForTextToSpeech.from_pretrained(model_name_or_path).to(device)
        self.model.eval()
        self.processor = SpeechT5Processor.from_pretrained(model_name_or_path, normalize=True)
        self.vocoder = SpeechT5HifiGan.from_pretrained(vocoder_model_name_or_path).to(device)
        self.vocoder.eval()

        # fetch default speaker embedding
        if os.path.exists("spk_embed_default.pt"):
            self.default_speaker_embedding = torch.load("spk_embed_default.pt")
        else:
            try:
                p = subprocess.Popen(
                    [
                        "curl",
                        "-O",
                        "https://raw.githubusercontent.com/intel/intel-extension-for-transformers/main/"
                        "intel_extension_for_transformers/neural_chat/assets/speaker_embeddings/"
                        "spk_embed_default.pt",
                    ]
                )
                p.wait()
                self.default_speaker_embedding = torch.load("spk_embed_default.pt")
            except Exception as e:
                print("Warning! Need to prepare speaker_embeddings, will use the backup embedding.")
                self.default_speaker_embedding = torch.zeros((1, 512))

        if self.device == "hpu":
            # do hpu graph warmup with variable inputs
            self._warmup_speecht5_hpu_graph()

    def split_long_text_into_batch(self, text, batch_length=128):
        """Batch the long text into sequences of shorter sentences."""
        res = []
        hitted_ends = [",", ".", "?", "!", "。", ";", " "]
        idx = 0
        cur_start = 0
        cur_end = -1
        while idx < len(text):
            if idx - cur_start > batch_length:
                if cur_end != -1 and cur_end > cur_start:
                    res.append(text[cur_start : cur_end + 1])
                else:
                    cur_end = cur_start + batch_length - 1
                    res.append(text[cur_start : cur_end + 1])
                idx = cur_end
                cur_start = cur_end + 1
            if text[idx] in hitted_ends:
                cur_end = idx
            idx += 1
        # deal with the last sequence
        res.append(text[cur_start:idx])
        res = [i + "." for i in res]  # avoid unexpected end of sequence
        return res

    def _warmup_speecht5_hpu_graph(self):
        self.t2s("Hello, how can I help you today?")
        self.t2s("OPEA is an ecosystem orchestration framework to integrate performant GenAI technologies.")
        self.t2s(
            "OPEA is an ecosystem orchestration framework to integrate performant GenAI technologies & workflows leading to quicker GenAI adoption and business value."
        )

    def t2s(self, text):
        if self.device == "hpu":
            # See https://github.com/huggingface/optimum-habana/pull/824
            from optimum.habana.utils import set_seed

            set_seed(555)
        all_speech = np.array([])
        text = self.split_long_text_into_batch(text, batch_length=100)
        inputs = self.processor(text=text, padding=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            waveforms, waveform_lengths = self.model.generate_speech(
                inputs["input_ids"].to(self.device),
                speaker_embeddings=self.default_speaker_embedding.to(self.device),
                attention_mask=inputs["attention_mask"].to(self.device),
                vocoder=self.vocoder,
                return_output_lengths=True,
            )
        for i in range(waveforms.size(0)):
            all_speech = np.concatenate([all_speech, waveforms[i][: waveform_lengths[i]].cpu().numpy()])

        return all_speech
