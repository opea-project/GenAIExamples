# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
import urllib.request

import numpy as np
import torch
from datasets import Audio, Dataset
from pydub import AudioSegment


class WhisperModel:
    """Convert audio to text."""

    def __init__(
        self,
        model_name_or_path="openai/whisper-small",
        language="english",
        device="cpu",
        hpu_max_len=8192,
        return_timestamps=False,
    ):
        if device == "hpu":
            # Explicitly link HPU with Torch
            from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

            adapt_transformers_to_gaudi()
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        self.device = device
        self.asr_model_name_or_path = os.environ.get("ASR_MODEL_PATH", model_name_or_path)
        print("Downloading model: {}".format(self.asr_model_name_or_path))
        self.model = WhisperForConditionalGeneration.from_pretrained(self.asr_model_name_or_path).to(self.device)
        self.processor = WhisperProcessor.from_pretrained(self.asr_model_name_or_path)
        self.model.eval()

        self.language = language
        self.hpu_max_len = hpu_max_len
        self.return_timestamps = return_timestamps

        if device == "hpu":
            self._warmup_whisper_hpu_graph("https://github.com/Spycsh/assets/raw/main/ljspeech_60s_audio.wav")
            self._warmup_whisper_hpu_graph("https://github.com/Spycsh/assets/raw/main/ljspeech_30s_audio.wav")

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

        try:
            processed_inputs = self.processor(
                waveform,
                return_tensors="pt",
                truncation=False,
                padding="longest",
                return_attention_mask=True,
                sampling_rate=16000,
            )
        except RuntimeError as e:
            if "Padding size should be less than" in str(e):
                # short-form
                processed_inputs = self.processor(
                    waveform,
                    return_tensors="pt",
                    sampling_rate=16000,
                )
            else:
                raise e

        if processed_inputs.input_features.shape[-1] < 3000:
            # short-form
            processed_inputs = self.processor(
                waveform,
                return_tensors="pt",
                sampling_rate=16000,
            )
        else:
            processed_inputs["input_features"] = torch.nn.functional.pad(
                processed_inputs.input_features,
                (0, self.hpu_max_len - processed_inputs.input_features.size(-1)),
                value=-1.5,
            )
            processed_inputs["attention_mask"] = torch.nn.functional.pad(
                processed_inputs.attention_mask,
                (0, self.hpu_max_len + 1 - processed_inputs.attention_mask.size(-1)),
                value=0,
            )

        _ = self.model.generate(
            **(
                processed_inputs.to(
                    self.device,
                )
            ),
            language=self.language,
            return_timestamps=self.return_timestamps,
        )

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

        try:
            processed_inputs = self.processor(
                waveform,
                return_tensors="pt",
                truncation=False,
                padding="longest",
                return_attention_mask=True,
                sampling_rate=16000,
            )
        except RuntimeError as e:
            if "Padding size should be less than" in str(e):
                # short-form
                processed_inputs = self.processor(
                    waveform,
                    return_tensors="pt",
                    sampling_rate=16000,
                )
            else:
                raise e
        if processed_inputs.input_features.shape[-1] < 3000:
            # short-form
            processed_inputs = self.processor(
                waveform,
                return_tensors="pt",
                sampling_rate=16000,
            )
        elif self.device == "hpu" and processed_inputs.input_features.shape[-1] > 3000:
            processed_inputs["input_features"] = torch.nn.functional.pad(
                processed_inputs.input_features,
                (0, self.hpu_max_len - processed_inputs.input_features.size(-1)),
                value=-1.5,
            )
            processed_inputs["attention_mask"] = torch.nn.functional.pad(
                processed_inputs.attention_mask,
                (0, self.hpu_max_len + 1 - processed_inputs.attention_mask.size(-1)),
                value=0,
            )

        predicted_ids = self.model.generate(
            **(
                processed_inputs.to(
                    self.device,
                )
            ),
            language=self.language,
            return_timestamps=self.return_timestamps,
        )
        # pylint: disable=E1101
        result = self.processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True, normalize=True)[0]
        if self.language in ["chinese", "mandarin"]:
            from zhconv import convert

            result = convert(result, "zh-cn")
        print(f"generated text in {time.time() - start} seconds, and the result is: {result}")
        return result


if __name__ == "__main__":
    asr = WhisperModel(
        model_name_or_path="openai/whisper-small", language="english", device="cpu", return_timestamps=True
    )

    # Test multilanguage asr
    asr.language = "chinese"
    urllib.request.urlretrieve(
        "https://paddlespeech.bj.bcebos.com/Parakeet/docs/demos/labixiaoxin.wav",
        "sample.wav",
    )
    text = asr.audio2text("sample.wav")

    asr.language = "english"
    urllib.request.urlretrieve(
        "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav",
        "sample.wav",
    )
    text = asr.audio2text("sample.wav")

    for i in [5, 10, 30, 60]:
        urllib.request.urlretrieve(f"https://github.com/Spycsh/assets/raw/main/ljspeech_{i}s_audio.wav", "sample.wav")
        text = asr.audio2text("sample.wav")
