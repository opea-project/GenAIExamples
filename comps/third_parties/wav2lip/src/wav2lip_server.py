# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2013--2023, librosa development team.
# Copyright 1999-2003 The OpenLDAP Foundation, Redwood City, California, USA.  All Rights Reserved.
# Copyright (c) 2012, Anaconda, Inc. All rights reserved.

import os

import cv2
import ffmpeg
import numpy as np

# FastAPI
import uvicorn

# Wav2Lip-GFPGAN
import Wav2Lip.audio as audio
from fastapi import FastAPI, Request
from fastapi.responses import Response
from utils import *

app = FastAPI()
model = None


@app.get("/v1/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/v1/wav2lip")
async def animate(request: Request):
    print("Animation generation begins.")

    # Wait for request
    request_dict = await request.json()
    audio_b64_str = request_dict.pop("audio")

    if not os.path.exists("inputs"):
        os.makedirs("inputs")
    if not os.path.exists("temp"):
        os.makedirs("temp")
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    if not os.path.isfile(args.face):
        raise ValueError("--face argument must be a valid path to video/image file")
    elif args.face.split(".")[-1] in ["jpg", "jpeg", "png"]:
        full_frames = [cv2.imread(args.face)]
        fps = args.fps
    else:
        video_stream = cv2.VideoCapture(args.face)
        fps = video_stream.get(cv2.CAP_PROP_FPS)
        print("Reading video frames...")
        full_frames = []
        while True:
            still_reading, frame = video_stream.read()
            if not still_reading:
                video_stream.release()
                break
            if args.resize_factor > 1:
                frame = cv2.resize(frame, (frame.shape[1] // args.resize_factor, frame.shape[0] // args.resize_factor))
            if args.rotate:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE())

            y1, y2, x1, x2 = args.crop
            if x2 == -1:
                x2 = frame.shape[1]
            if y2 == -1:
                y2 = frame.shape[0]
            frame = frame[y1:y2, x1:x2]
            full_frames.append(frame)

    print("Number of frames available for inference: " + str(len(full_frames)))

    if args.audio != "None":
        if not args.audio.endswith(".wav"):
            os.makedirs("temp", exist_ok=True)
            print("Extracting raw audio...")
            # command = f"ffmpeg -y -i {args.audio} -strict -2 temp/temp.wav"
            # subprocess.call(command, shell=True)

            ffmpeg.input(args.audio).output("temp/temp.wav", strict="-2").run(overwrite_output=True)
            args.audio = "temp/temp.wav"
    else:
        print(f"Signature for your audio: {audio_b64_str[:100]}")
        sr, y = base64_to_int16_to_wav(audio_b64_str, "temp/temp.wav")
        args.audio = "temp/temp.wav"

    wav = audio.load_wav(args.audio, 16000)
    mel = audio.melspectrogram(wav)
    print("Mel spectrogram shape: " + str(mel.shape))
    if np.isnan(mel.reshape(-1)).sum() > 0:
        raise ValueError("Mel contains nan! Using a TTS voice? Add a small epsilon noise to the wav file and try again")

    # one single video frame corresponds to 80/25*0.01 = 0.032 seconds (or 32 milliseconds) of audio
    mel_chunks = []
    mel_idx_multiplier = 80.0 / fps
    i = 0
    mel_step_size = 16
    while True:
        start_idx = int(i * mel_idx_multiplier)
        if start_idx + mel_step_size > len(mel[0]):
            mel_chunks.append(mel[:, len(mel[0]) - mel_step_size :])
            break
        mel_chunks.append(mel[:, start_idx : start_idx + mel_step_size])
        i += 1
    print(f"Length of mel chunks: {len(mel_chunks)}")

    full_frames = full_frames[: len(mel_chunks)]

    batch_size = args.wav2lip_batch_size
    gen = datagen(args, full_frames.copy(), mel_chunks)

    # iterate over the generator
    with torch.no_grad():
        for i, (img_batch, mel_batch, frames, coords) in enumerate(
            tqdm(gen, total=int(np.ceil(float(len(mel_chunks)) / batch_size)))
        ):
            if i == 0:
                frame_h, frame_w = full_frames[0].shape[:-1]
                if args.inference_mode == "wav2lip_only":
                    out = cv2.VideoWriter("temp/result.avi", cv2.VideoWriter_fourcc(*"DIVX"), fps, (frame_w, frame_h))
                else:
                    out = cv2.VideoWriter(
                        "temp/result.avi",
                        cv2.VideoWriter_fourcc(*"DIVX"),
                        fps,
                        (frame_w * args.upscale, frame_h * args.upscale),
                    )

            img_batch = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
            mel_batch = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)

            with torch.autocast(device_type=args.device, dtype=torch.bfloat16):
                pred = model(mel_batch, img_batch)

            pred = pred.cpu().to(torch.float32).numpy().transpose(0, 2, 3, 1) * 255.0

            for p, f, c in tqdm(zip(pred, frames, coords), total=pred.shape[0]):
                y1, y2, x1, x2 = c
                p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))
                f[y1:y2, x1:x2] = p  # patching

                # restore faces and background if necessary
                if args.inference_mode == "wav2lip+gfpgan":
                    cropped_faces, restored_faces, f = model_restorer.enhance(
                        f, has_aligned=args.aligned, only_center_face=args.only_center_face, paste_back=True
                    )
                out.write(f)
    out.release()

    ffmpeg.output(
        ffmpeg.input(args.audio),
        ffmpeg.input("temp/result.avi"),
        args.outfile,
        strict="-2",
        crf=23,
        vcodec="libx264",
        preset="medium",
        acodec="aac",
    ).run(overwrite_output=True)

    args.audio = "None"  # IMPORTANT: Reset audio to None for the next audio request

    return {"wav2lip_result": args.outfile}


if __name__ == "__main__":
    # Load arguments
    args = get_args()
    print("args: ", args)

    # Specify device
    # Habana
    if args.device == "hpu":
        import habana_frameworks.torch.core as htcore
        import habana_frameworks.torch.hpu as hthpu

        if hthpu.is_available():
            device = "hpu"
        else:
            device = "cpu"
    elif args.device == "cuda":
        device = "cuda"
    else:
        device = "cpu"
        print("Invalid device argument, fall back to cpu")
    print("Using {} for inference.".format(device))

    # Load Wav2Lip, BG sampler, GFPGAN models
    model = load_model(args)
    print("Wav2Lip Model loaded")

    if args.inference_mode == "wav2lip+gfpgan" and args.bg_upsampler == "realesrgan":
        model_bg_upsampler = load_bg_upsampler(args)
        print("Model BG Sampler loaded")
    else:
        model_bg_upsampler = None
        print("Model BG Sampler not loaded")

    # load GFPGAN model if needed
    if args.inference_mode == "wav2lip+gfpgan":
        model_restorer = load_gfpgan(args, model_bg_upsampler)
        print("Model GFPGAN and face helper loaded")
    else:
        model_restorer = None
        print("Model GFPGAN not loaded")

    # Run FastAPI
    uvicorn.run(app, host=args.host, port=args.port)
