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

import contextlib
import os
import time

import numpy as np
import torch
from datasets import Audio, Dataset
from pydub import AudioSegment
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from comps import Audio2TextDoc, TextDoc, opea_microservices, register_microservice


def _audiosegment_to_librosawav(audiosegment):
    channel_sounds = audiosegment.split_to_mono()[:1]  # only select the first channel
    samples = [s.get_array_of_samples() for s in channel_sounds]

    fp_arr = np.array(samples).T.astype(np.float32)
    fp_arr /= np.iinfo(samples[0].typecode).max
    fp_arr = fp_arr.reshape(-1)

    return fp_arr


def audio2text(
    audio_path,
    model_name_or_path="openai/whisper-small",
    language=None,
    bf16=False,
    device="cpu",
):
    """Convert audio to text."""
    start = time.time()
    model = WhisperForConditionalGeneration.from_pretrained(model_name_or_path).to(device)
    processor = WhisperProcessor.from_pretrained(model_name_or_path)
    model.eval()
    bf16 = bf16
    if bf16:
        import intel_extension_for_pytorch as ipex

        model = ipex.optimize(model, dtype=torch.bfloat16)
    language = language

    try:
        waveform = AudioSegment.from_file(audio_path).set_frame_rate(16000)
        waveform = _audiosegment_to_librosawav(waveform)
    except Exception as e:
        print(f"[ASR] audiosegment to librosa wave fail: {e}")
        audio_dataset = Dataset.from_dict({"audio": [audio_path]}).cast_column("audio", Audio(sampling_rate=16000))
        waveform = audio_dataset[0]["audio"]["array"]

    inputs = processor.feature_extractor(waveform, return_tensors="pt", sampling_rate=16_000).input_features.to(device)
    with torch.cpu.amp.autocast() if bf16 else contextlib.nullcontext():
        if language is None:
            predicted_ids = model.generate(inputs)
        elif language == "auto":
            model.config.forced_decoder_ids = None
            predicted_ids = model.generate(inputs)
        else:
            forced_decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
            model.config.forced_decoder_ids = forced_decoder_ids
            predicted_ids = model.generate(inputs)

    result = processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True, normalize=True)[0]
    if language == "auto" or language == "zh":
        from zhconv import convert

        result = convert(result, "zh-cn")
    print(f"generated text in {time.time() - start} seconds, and the result is: {result}")
    return result


@register_microservice(
    name="opea_service@asr",
    expose_endpoint="/v1/audio/transcriptions",
    port=9099,
    input_datatype=Audio2TextDoc,
    output_datatype=TextDoc,
)
async def audio_to_text(audio: Audio2TextDoc):
    audio.tensor, audio.frame_rate = audio.url.load()  # AudioNdArray, fr
    audio_path = f"{audio.id}.wav"
    audio.tensor.save(audio_path, frame_rate=16000)

    try:
        asr_result = audio2text(audio_path, model_name_or_path=audio.model_name_or_path, language=audio.language)
    except Exception as e:
        print(e)
        asr_result = e
    finally:
        os.remove(audio_path)
    res = TextDoc(text=asr_result)
    return res


if __name__ == "__main__":
    print("[asr - router] ASR initialized.")
    opea_microservices["opea_service@asr"].start()
