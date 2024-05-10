# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import os
import time
from io import BytesIO

import numpy as np
import torch
from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor

from comps import Base64ByteStrDoc, TextDoc, opea_microservices, opea_telemetry, register_microservice


@opea_telemetry
def split_long_text_into_batch(text, batch_length=64):
    """Batch the long text into sequences of shorter sentences."""
    res = []
    hitted_ends = [",", ".", "?", "!", "。", ";"]
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


@opea_telemetry
def text2speech(
    text,
    model_name_or_path="microsoft/speecht5_tts",
    vocoder_model_name_or_path="microsoft/speecht5_hifigan",
    output_audio_path="./response.wav",
    device="cpu",
):
    start = time.time()
    model = SpeechT5ForTextToSpeech.from_pretrained(model_name_or_path).to(device)
    model.eval()
    processor = SpeechT5Processor.from_pretrained(model_name_or_path, normalize=True)
    vocoder = SpeechT5HifiGan.from_pretrained(vocoder_model_name_or_path).to(device)
    vocoder.eval()

    if os.path.exists("spk_embed_default.pt"):
        default_speaker_embedding = torch.load("spk_embed_default.pt")
    else:  # pragma: no cover
        import subprocess

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
            default_speaker_embedding = torch.load("spk_embed_default.pt")
        except Exception as e:
            print("Warning! Need to prepare speaker_embeddings, will use the backup embedding.")
            default_speaker_embedding = torch.zeros((1, 512))

    all_speech = np.array([])
    text = split_long_text_into_batch(text, batch_length=64)
    inputs = processor(text=text, padding=True, max_length=128, return_tensors="pt")
    with torch.no_grad():
        waveforms, waveform_lengths = model.generate_speech(
            inputs["input_ids"].to(device),
            speaker_embeddings=default_speaker_embedding.to(device),
            attention_mask=inputs["attention_mask"].to(device),
            vocoder=vocoder,
            return_output_lengths=True,
        )
    for i in range(waveforms.size(0)):
        all_speech = np.concatenate([all_speech, waveforms[i][: waveform_lengths[i]].cpu().numpy()])
        all_speech = np.concatenate([all_speech, np.array([0 for i in range(4000)])])  # pad after each end

    print(f"generated speech in {time.time() - start} seconds")
    return all_speech


@register_microservice(
    name="opea_service@tts",
    expose_endpoint="/v1/audio/speech",
    host="0.0.0.0",
    port=9999,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
@opea_telemetry
async def text_to_audio(input: TextDoc):
    text = input.text
    speech = text2speech(text=text)
    buffered = BytesIO()
    buffered.write(speech.tobytes())
    return Base64ByteStrDoc(byte_str=base64.b64encode(buffered.getvalue()))


if __name__ == "__main__":
    print("[tts - router] TTS initialized.")
    opea_microservices["opea_service@tts"].start()
