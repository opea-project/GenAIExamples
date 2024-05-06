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

from comps import Base64ByteStrDoc, TextDoc, opea_microservices, register_microservice


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
    inputs = processor(text=text, return_tensors="pt")
    with torch.no_grad():
        spectrogram = model.generate_speech(inputs["input_ids"].to(device), default_speaker_embedding.to(device))
        speech = vocoder(spectrogram)
        all_speech = np.concatenate([all_speech, speech.cpu().numpy()])
        all_speech = np.concatenate([all_speech, np.array([0 for i in range(8000)])])  # pad after each end
    print(f"generated speech in {time.time() - start} seconds")
    return all_speech


@register_microservice(
    name="opea_service@tts",
    expose_endpoint="/v1/audio/speech",
    port=9999,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
async def text_to_audio(input: TextDoc):
    text = input.text
    speech = text2speech(text=text)
    buffered = BytesIO()
    buffered.write(speech.tobytes())
    return Base64ByteStrDoc(byte_str=base64.b64encode(buffered.getvalue()))


if __name__ == "__main__":
    print("[tts - router] TTS initialized.")
    opea_microservices["opea_service@tts"].start()
