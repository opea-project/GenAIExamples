#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This script is adapted from
# https://github.com/RVC-Boss/GPT-SoVITS/blob/main/api.py
# which is under the MIT license
#
# Copyright (c) 2024 RVC-Boss
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import base64
import contextlib
import logging
import os
import re
import signal
import subprocess
import sys
from io import BytesIO
from time import time as ttime

import config as global_config
import LangSegment
import librosa
import numpy as np
import soundfile as sf
import torch
import uvicorn
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from feature_extractor import cnhubert
from module.mel_processing import spectrogram_torch
from module.models import SynthesizerTrn
from my_utils import load_audio
from starlette.middleware.cors import CORSMiddleware
from text import cleaned_text_to_sequence
from text.cleaner import clean_text
from transformers import AutoModelForMaskedLM, AutoTokenizer


class DefaultRefer:
    def __init__(self, path, text, language):
        self.path = args.default_refer_path
        self.text = args.default_refer_text
        self.language = args.default_refer_language

    def is_ready(self) -> bool:
        return is_full(self.path, self.text, self.language)


def is_empty(*items):
    for item in items:
        if item is not None and item != "":
            return False
    return True


def is_full(*items):
    for item in items:
        if item is None or item == "":
            return False
    return True


def change_sovits_weights(sovits_path):
    global vq_model, hps
    dict_s2 = torch.load(sovits_path, map_location="cpu")
    hps = dict_s2["config"]
    hps = DictToAttrRecursive(hps)
    hps.model.semantic_frame_rate = "25hz"
    vq_model = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model,
    )
    if "pretrained" not in sovits_path:
        del vq_model.enc_q
    if is_half:
        vq_model = vq_model.half().to(device)
    else:
        vq_model = vq_model.to(device)
    vq_model.eval()
    vq_model.load_state_dict(dict_s2["weight"], strict=False)


def change_gpt_weights(gpt_path):
    global hz, max_sec, t2s_model, config
    hz = 50
    dict_s1 = torch.load(gpt_path, map_location="cpu")
    config = dict_s1["config"]
    max_sec = config["data"]["max_sec"]
    t2s_model = Text2SemanticLightningModule(config, "****", is_train=False)
    t2s_model.load_state_dict(dict_s1["weight"])
    if is_half:
        t2s_model = t2s_model.half()
    t2s_model = t2s_model.to(device)
    t2s_model.eval()
    total = sum([param.nelement() for param in t2s_model.parameters()])
    logger.info("Number of parameter: %.2fM" % (total / 1e6))


def get_bert_feature(text, word2ph):
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt")
        for i in inputs:
            inputs[i] = inputs[i].to(device)
        res = bert_model(**inputs, output_hidden_states=True)
        res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
    assert len(word2ph) == len(text)
    phone_level_feature = []
    for i in range(len(word2ph)):
        repeat_feature = res[i].repeat(word2ph[i], 1)
        phone_level_feature.append(repeat_feature)
    phone_level_feature = torch.cat(phone_level_feature, dim=0)
    return phone_level_feature.T


def clean_text_inf(text, language):
    phones, word2ph, norm_text = clean_text(text, language)
    phones = cleaned_text_to_sequence(phones)
    return phones, word2ph, norm_text


def get_bert_inf(phones, word2ph, norm_text, language):
    language = language.replace("all_", "")
    if language == "zh":
        bert = get_bert_feature(norm_text, word2ph).to(device)
    else:
        bert = torch.zeros(
            (1024, len(phones)),
            dtype=torch.float16 if is_half else torch.float32,
        ).to(device)

    return bert


def get_phones_and_bert(text, language):
    if language in {"en", "all_zh", "all_ja"}:
        language = language.replace("all_", "")
        if language == "en":
            LangSegment.setfilters(["en"])
            formattext = " ".join(tmp["text"] for tmp in LangSegment.getTexts(text))
        else:
            formattext = text
        while "  " in formattext:
            formattext = formattext.replace("  ", " ")
        phones, word2ph, norm_text = clean_text_inf(formattext, language)
        if language == "zh":
            bert = get_bert_feature(norm_text, word2ph).to(device)
        else:
            bert = torch.zeros(
                (1024, len(phones)),
                dtype=torch.float16 if is_half else torch.float32,
            ).to(device)
    elif language in {"zh", "ja", "auto"}:
        textlist = []
        langlist = []
        LangSegment.setfilters(["zh", "ja", "en", "ko"])
        if language == "auto":
            for tmp in LangSegment.getTexts(text):
                if tmp["lang"] == "ko":
                    langlist.append("zh")
                    textlist.append(tmp["text"])
                else:
                    langlist.append(tmp["lang"])
                    textlist.append(tmp["text"])
        else:
            for tmp in LangSegment.getTexts(text):
                if tmp["lang"] == "en":
                    langlist.append(tmp["lang"])
                else:
                    langlist.append(language)
                textlist.append(tmp["text"])

        phones_list = []
        bert_list = []
        norm_text_list = []
        for i in range(len(textlist)):
            lang = langlist[i]
            phones, word2ph, norm_text = clean_text_inf(textlist[i], lang)
            bert = get_bert_inf(phones, word2ph, norm_text, lang)
            phones_list.append(phones)
            norm_text_list.append(norm_text)
            bert_list.append(bert)
        bert = torch.cat(bert_list, dim=1)
        phones = sum(phones_list, [])
        norm_text = "".join(norm_text_list)

    return phones, bert.to(torch.float16 if is_half else torch.float32), norm_text


class DictToAttrRecursive:
    def __init__(self, input_dict):
        for key, value in input_dict.items():
            if isinstance(value, dict):
                setattr(self, key, DictToAttrRecursive(value))
            else:
                setattr(self, key, value)


def get_spepc(hps, filename):
    audio = load_audio(filename, int(hps.data.sampling_rate))
    audio = torch.FloatTensor(audio)
    audio_norm = audio
    audio_norm = audio_norm.unsqueeze(0)
    spec = spectrogram_torch(
        audio_norm,
        hps.data.filter_length,
        hps.data.sampling_rate,
        hps.data.hop_length,
        hps.data.win_length,
        center=False,
    )
    return spec


def pack_audio(audio_bytes, data, rate):
    if media_type == "ogg":
        audio_bytes = pack_ogg(audio_bytes, data, rate)
    elif media_type == "aac":
        audio_bytes = pack_aac(audio_bytes, data, rate)
    else:
        audio_bytes = pack_raw(audio_bytes, data, rate)

    return audio_bytes


def pack_ogg(audio_bytes, data, rate):
    with sf.SoundFile(audio_bytes, mode="w", samplerate=rate, channels=1, format="ogg") as audio_file:
        audio_file.write(data)

    return audio_bytes


def pack_raw(audio_bytes, data, rate):
    audio_bytes.write(data.tobytes())

    return audio_bytes


def pack_wav(audio_bytes, rate):
    data = np.frombuffer(audio_bytes.getvalue(), dtype=np.int16)
    wav_bytes = BytesIO()
    sf.write(wav_bytes, data, rate, format="wav")

    return wav_bytes


def pack_aac(audio_bytes, data, rate):
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-f",
            "s16le",
            "-ar",
            str(rate),
            "-ac",
            "1",
            "-i",
            "pipe:0",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-vn",
            "-f",
            "adts",
            "pipe:1",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, _ = process.communicate(input=data.tobytes())
    audio_bytes.write(out)

    return audio_bytes


def read_clean_buffer(audio_bytes):
    audio_chunk = audio_bytes.getvalue()
    audio_bytes.truncate(0)
    audio_bytes.seek(0)

    return audio_bytes, audio_chunk


def cut_text(text, punc):
    punc_list = [p for p in punc if p in {",", ".", ";", "?", "!", "、", "，", "。", "？", "！", ";", "：", "…"}]
    if len(punc_list) > 0:
        punds = r"[" + "".join(punc_list) + r"]"
        text = text.strip("\n")
        items = re.split(f"({punds})", text)
        mergeitems = ["".join(group) for group in zip(items[::2], items[1::2])]
        if len(items) % 2 == 1:
            mergeitems.append(items[-1])
        text = "\n".join(mergeitems)

    while "\n\n" in text:
        text = text.replace("\n\n", "\n")

    return text


def only_punc(text):
    return not any(t.isalnum() or t.isalpha() for t in text)


def get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language):
    t0 = ttime()
    prompt_text = prompt_text.strip("\n")
    prompt_language, text = prompt_language, text.strip("\n")
    zero_wav = np.zeros(int(hps.data.sampling_rate * 0.3), dtype=np.float16 if is_half else np.float32)
    with torch.no_grad():
        wav16k, sr = librosa.load(ref_wav_path, sr=16000)
        wav16k = torch.from_numpy(wav16k)
        zero_wav_torch = torch.from_numpy(zero_wav)
        if is_half:
            wav16k = wav16k.half().to(device)
            zero_wav_torch = zero_wav_torch.half().to(device)
        else:
            wav16k = wav16k.to(device)
            zero_wav_torch = zero_wav_torch.to(device)
        wav16k = torch.cat([wav16k, zero_wav_torch])
        ssl_content = ssl_model.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)  # .float()
        codes = vq_model.extract_latent(ssl_content)
        prompt_semantic = codes[0, 0]
    t1 = ttime()
    prompt_language = dict_language[prompt_language.lower()]
    text_language = dict_language[text_language.lower()]
    phones1, bert1, norm_text1 = get_phones_and_bert(prompt_text, prompt_language)
    texts = text.split("\n")
    audio_bytes = BytesIO()

    for text in texts:
        if only_punc(text):
            continue

        audio_opt = []
        phones2, bert2, norm_text2 = get_phones_and_bert(text, text_language)
        bert = torch.cat([bert1, bert2], 1)

        all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(device).unsqueeze(0)
        bert = bert.to(device).unsqueeze(0)
        all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)
        prompt = prompt_semantic.unsqueeze(0).to(device)
        # import intel_extension_for_pytorch as ipex
        # ipex.optimize(t2s_model.model)
        # from torch import profiler
        t2 = ttime()
        with torch.no_grad():
            # with profiler.profile(record_shapes=True) as prof:
            #     with profiler.record_function("model_inference"):
            with (
                torch.cpu.amp.autocast(enabled=True, dtype=torch.bfloat16, cache_enabled=True)
                if use_bf16
                else contextlib.nullcontext()
            ):
                pred_semantic, idx = t2s_model.model.infer_panel(
                    all_phoneme_ids,
                    all_phoneme_len,
                    prompt,
                    bert,
                    # prompt_phone_len=ph_offset,
                    top_k=config["inference"]["top_k"],
                    early_stop_num=hz * max_sec,
                )
            # print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))
        t3 = ttime()
        pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)
        refer = get_spepc(hps, ref_wav_path)
        if is_half:
            refer = refer.half().to(device)
        else:
            refer = refer.to(device)
        audio = (
            vq_model.decode(pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0), refer)
            .detach()
            .cpu()
            .numpy()[0, 0]
        )
        audio_opt.append(audio)
        audio_opt.append(zero_wav)
        t4 = ttime()
        audio_bytes = pack_audio(
            audio_bytes, (np.concatenate(audio_opt, 0) * 32768).astype(np.int16), hps.data.sampling_rate
        )
        logger.info("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t3 - t2, t4 - t3))
        if stream_mode == "normal":
            audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
            yield audio_chunk

    if not stream_mode == "normal":
        if media_type == "wav":
            audio_bytes = pack_wav(audio_bytes, hps.data.sampling_rate)
        yield audio_bytes.getvalue()


def handle_control(command):
    if command == "restart":
        os.execl(g_config.python_exec, g_config.python_exec, *sys.argv)
    elif command == "exit":
        os.kill(os.getpid(), signal.SIGTERM)
        exit(0)


def handle_change(path, text, language):
    if is_empty(path, text, language):
        return JSONResponse(
            {"code": 400, "message": 'missing any of the following parameters: "path", "text", "language"'},
            status_code=400,
        )

    if path != "" or path is not None:
        default_refer.path = path
    if text != "" or text is not None:
        default_refer.text = text
    if language != "" or language is not None:
        default_refer.language = language

    logger.info(f"current default reference audio path: {default_refer.path}")
    logger.info(f"current default reference audio text: {default_refer.text}")
    logger.info(f"current default reference audio language: {default_refer.language}")
    logger.info(f"is_ready: {default_refer.is_ready()}")

    return JSONResponse({"code": 0, "message": "Success"}, status_code=200)


def text_stream_generator(result):
    """Embed the unicode byte values to base64 and yield the text stream with data prefix.

    Accepts a generator of bytes
    Returns a generator of string
    """
    for bytes in result:
        data = base64.b64encode(bytes)
        yield f"data: {data}\n\n"
    yield "data: [DONE]\n\n"


def handle(refer_wav_path, prompt_text, prompt_language, text, text_language, cut_punc):
    if (
        refer_wav_path == ""
        or refer_wav_path is None
        or prompt_text == ""
        or prompt_text is None
        or prompt_language == ""
        or prompt_language is None
    ):
        refer_wav_path, prompt_text, prompt_language = (
            default_refer.path,
            default_refer.text,
            default_refer.language,
        )
        if not default_refer.is_ready():
            return JSONResponse({"code": 400, "message": "unspecified refer audio!"}, status_code=400)

    if cut_punc is None:
        text = cut_text(text, default_cut_punc)
    else:
        text = cut_text(text, cut_punc)

    if not return_text_stream:
        return StreamingResponse(
            get_tts_wav(refer_wav_path, prompt_text, prompt_language, text, text_language),
            media_type="audio/" + media_type,
        )
    else:
        result = get_tts_wav(refer_wav_path, prompt_text, prompt_language, text, text_language)

        return StreamingResponse(text_stream_generator(result), media_type="text/event-stream")


# --------------------------------
# Initialization part
# --------------------------------
now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append("%s/GPT_SoVITS" % (now_dir))

dict_language = {
    "中文": "all_zh",
    "英文": "en",
    "日文": "all_ja",
    "中英混合": "zh",
    "日英混合": "ja",
    "多语种混合": "auto",
    "all_zh": "all_zh",
    "en": "en",
    "all_ja": "all_ja",
    "zh": "zh",
    "ja": "ja",
    "auto": "auto",
}

logging.config.dictConfig(uvicorn.config.LOGGING_CONFIG)
logger = logging.getLogger("uvicorn")

g_config = global_config.Config()

parser = argparse.ArgumentParser(description="GPT-SoVITS api")

parser.add_argument("-s", "--sovits_path", type=str, default=g_config.sovits_path, help="SoVITS model path")
parser.add_argument("-g", "--gpt_path", type=str, default=g_config.gpt_path, help="GPT model path")
parser.add_argument("-dr", "--default_refer_path", type=str, default="", help="default reference audio path")
parser.add_argument("-dt", "--default_refer_text", type=str, default="", help="default reference audio text")
parser.add_argument("-dl", "--default_refer_language", type=str, default="", help="default reference audio language")
parser.add_argument("-d", "--device", type=str, default=g_config.infer_device, help="cuda / cpu")
parser.add_argument("-a", "--bind_addr", type=str, default="0.0.0.0", help="default: 0.0.0.0")
parser.add_argument("-p", "--port", type=int, default=g_config.api_port, help="default: 9880")
parser.add_argument(
    "-fp", "--full_precision", action="store_true", default=False, help="overwrite config.is_half, use fp32"
)
parser.add_argument(
    "-hp", "--half_precision", action="store_true", default=False, help="overwrite config.is_half, use fp16"
)
# Here add an argument for specifying torch.bfloat16 inference on Xeon CPU
parser.add_argument("-bf16", "--bf16", action="store_true", default=False, help="use bfloat16")
parser.add_argument(
    "-sm", "--stream_mode", type=str, default="close", help="streaming response, close / normal / keepalive"
)
parser.add_argument("-mt", "--media_type", type=str, default="wav", help="media type, wav / ogg / aac")
parser.add_argument("-cp", "--cut_punc", type=str, default="", help="text splitter, among ,.;?!、，。？！;：…")
parser.add_argument(
    "-hb", "--hubert_path", type=str, default=g_config.cnhubert_path, help="overwrite config.cnhubert_path"
)
parser.add_argument("-b", "--bert_path", type=str, default=g_config.bert_path, help="overwrite config.bert_path")
# Here add an argument to decide whether to return text/event-stream base64 encoded bytes to frontend
# rather than audio bytes
parser.add_argument(
    "-rts",
    "--return_text_stream",
    action="store_true",
    default=False,
    help="whether to return text/event-stream base64 encoded bytes to frontend",
)

args = parser.parse_args()
sovits_path = args.sovits_path
gpt_path = args.gpt_path
device = args.device
port = args.port
host = args.bind_addr
cnhubert_base_path = args.hubert_path
bert_path = args.bert_path
default_cut_punc = args.cut_punc
return_text_stream = args.return_text_stream

# Set default reference configuration
default_refer = DefaultRefer(args.default_refer_path, args.default_refer_text, args.default_refer_language)

# Check model paths
if sovits_path == "":
    sovits_path = g_config.pretrained_sovits_path
    logger.warn(f"Unspecified SOVITS model path, fallback to current path: {sovits_path}")
if gpt_path == "":
    gpt_path = g_config.pretrained_gpt_path
    logger.warn(f"Unspecified GPT model path, fallback to current path: {gpt_path}")

if default_refer.path == "" or default_refer.text == "" or default_refer.language == "":
    default_refer.path, default_refer.text, default_refer.language = "", "", ""
    logger.info("Unspecified default refer audio")
else:
    logger.info(f"default refer audio path: {default_refer.path}")
    logger.info(f"default refer audio text: {default_refer.text}")
    logger.info(f"default refer audio language: {default_refer.language}")

# deal with half precision
if device == "cuda":
    is_half = g_config.is_half
    use_bf16 = False
    if args.full_precision:
        is_half = False
    if args.half_precision:
        is_half = True
    if args.full_precision and args.half_precision:
        is_half = g_config.is_half  # fallback to fp32
    logger.info(f"fp16 half: {is_half}")
else:
    is_half = False
    use_bf16 = g_config.use_bf16
    if args.full_precision:
        use_bf16 = False
    elif args.bf16:
        use_bf16 = True

    logger.info(f"bf16 half: {use_bf16}")

# stream response mode
if args.stream_mode.lower() in ["normal", "n"]:
    stream_mode = "normal"
    logger.info("stream response mode enabled")
else:
    stream_mode = "close"

# media type
if args.media_type.lower() in ["aac", "ogg"]:
    media_type = args.media_type.lower()
elif stream_mode == "close":
    media_type = "wav"
else:
    media_type = "ogg"
logger.info(f"media type: {media_type}")

# Initialize the model
cnhubert.cnhubert_base_path = cnhubert_base_path
tokenizer = AutoTokenizer.from_pretrained(bert_path)
bert_model = AutoModelForMaskedLM.from_pretrained(bert_path)
ssl_model = cnhubert.get_model()
if is_half:
    bert_model = bert_model.half().to(device)
    ssl_model = ssl_model.half().to(device)
else:
    bert_model = bert_model.to(device)
    ssl_model = ssl_model.to(device)
change_sovits_weights(sovits_path)
change_gpt_weights(gpt_path)


# --------------------------------
# APIs
# --------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.post("/set_model")
async def set_model(request: Request):
    json_post_raw = await request.json()
    global gpt_path
    gpt_path = json_post_raw.get("gpt_model_path")
    global sovits_path
    sovits_path = json_post_raw.get("sovits_model_path")
    logger.info("gptpath" + gpt_path + ";vitspath" + sovits_path)
    change_sovits_weights(sovits_path)
    change_gpt_weights(gpt_path)
    return "ok"


@app.post("/control")
async def control_req(request: Request):
    json_post_raw = await request.json()
    return handle_control(json_post_raw.get("command"))


@app.get("/control")
async def control(command: str = None):
    return handle_control(command)


@app.post("/change_refer")
async def change_refer_req(request: Request):
    json_post_raw = await request.json()
    return handle_change(
        json_post_raw.get("refer_wav_path"), json_post_raw.get("prompt_text"), json_post_raw.get("prompt_language")
    )


@app.get("/change_refer")
async def change_refer(refer_wav_path: str = None, prompt_text: str = None, prompt_language: str = None):
    return handle_change(refer_wav_path, prompt_text, prompt_language)


@app.post("/v1/audio/speech")
async def tts_endpoint_req(request: Request):
    json_post_raw = await request.json()
    return handle(
        json_post_raw.get("refer_wav_path"),
        json_post_raw.get("prompt_text"),
        json_post_raw.get("prompt_language"),
        json_post_raw.get("text"),
        json_post_raw.get("text_language"),
        json_post_raw.get("cut_punc"),
    )


@app.get("/v1/audio/speech")
async def tts_endpoint(
    refer_wav_path: str = None,
    prompt_text: str = None,
    prompt_language: str = None,
    text: str = None,
    text_language: str = None,
    cut_punc: str = None,
):
    return handle(refer_wav_path, prompt_text, prompt_language, text, text_language, cut_punc)


@app.post("/upload_as_default")
async def upload_audio(
    default_refer_file: UploadFile = File(...),
    default_refer_text: str = Form(...),
    default_refer_language: str = Form(...),
):
    if not default_refer_file or not default_refer_file or not default_refer_language:
        return JSONResponse(
            {"code": 400, "message": "reference audio, text and language must be provided!"}, status_code=400
        )
    name = default_refer_file.filename

    if name.endswith(".mp3") or name.endswith(".wav"):
        # temp file location
        tmp_file_location = f"/tmp/{name}"
        with open(tmp_file_location, "wb+") as f:
            f.write(default_refer_file.file.read())
        logger.info(f"reference audio saved at {tmp_file_location}!")
        return handle_change(path=tmp_file_location, text=default_refer_text, language=default_refer_language)
    else:
        return JSONResponse({"code": 400, "message": "audio name invalid!"}, status_code=400)


if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port, workers=1)
