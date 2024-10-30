# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# Author: Chun Tao
# Date: 2024-08-02

# %% Imports
import argparse

# audio
import base64
import io
import os
from glob import glob
from os import listdir, path

import cv2
import numpy as np
import soundfile as sf
import torch

# wav2lip
import Wav2Lip.audio as audio
import Wav2Lip.face_detection as face_detection

# gfpgan
from gfpgan import GFPGANer
from tqdm import tqdm
from Wav2Lip.models import Wav2Lip


def get_args():
    parser = argparse.ArgumentParser(description="Inference code to lip-sync videos in the wild using Wav2Lip models")
    # General config
    parser.add_argument("--device", type=str, choices=["hpu", "cpu", "cuda"], default="cpu")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument(
        "--inference_mode",
        type=str,
        choices=["wav2lip_only", "wav2lip+gfpgan"],
        default="wav2lip+gfpgan",
        help="whether to use just wav2lip or include gfpgan",
    )
    # Wav2Lip config
    parser.add_argument(
        "--checkpoint_path", type=str, help="Name of saved checkpoint to load weights from", required=True
    )
    parser.add_argument("--face", type=str, help="Filepath of video/image that contains faces to use", required=True)
    parser.add_argument(
        "--audio",
        type=str,
        default="None",
        help="Filepath of video/audio file to use as raw audio source",
        required=False,
    )
    parser.add_argument(
        "--outfile",
        type=str,
        help="Video path to save result. See default for an e.g.",
        default="results/result_voice.mp4",
    )
    parser.add_argument(
        "--static", type=bool, help="If True, then use only first video frame for inference", default=False
    )
    parser.add_argument(
        "--fps",
        type=float,
        help="Can be specified only if input is a static image (default: 25)",
        default=25.0,
        required=False,
    )
    parser.add_argument(
        "--pads",
        nargs="+",
        type=int,
        default=[0, 10, 0, 0],
        help="Padding (top, bottom, left, right). Please adjust to include chin at least",
    )
    parser.add_argument("--face_det_batch_size", type=int, help="Batch size for face detection", default=16)
    parser.add_argument("--wav2lip_batch_size", type=int, help="Batch size for Wav2Lip model(s)", default=128)
    parser.add_argument(
        "--resize_factor",
        default=1,
        type=int,
        help="Reduce the resolution by this factor. Sometimes, best results are obtained at 480p or 720p",
    )
    parser.add_argument(
        "--crop",
        nargs="+",
        type=int,
        default=[0, -1, 0, -1],
        help="Crop video to a smaller region (top, bottom, left, right). Applied after resize_factor and rotate arg. "
        "Useful if multiple face present. -1 implies the value will be auto-inferred based on height, width",
    )
    parser.add_argument(
        "--box",
        nargs="+",
        type=int,
        default=[-1, -1, -1, -1],
        help="Specify a constant bounding box for the face. Use only as a last resort if the face is not detected."
        "Also, might work only if the face is not moving around much. Syntax: (top, bottom, left, right).",
    )
    parser.add_argument(
        "--rotate",
        default=False,
        action="store_true",
        help="Sometimes videos taken from a phone can be flipped 90deg. If true, will flip video right by 90deg."
        "Use if you get a flipped result, despite feeding a normal looking video",
    )
    parser.add_argument(
        "--nosmooth",
        default=False,
        action="store_true",
        help="Prevent smoothing face detections over a short temporal window",
    )
    # GFPGAN
    parser.add_argument(
        "-i", "--input", type=str, default="inputs/whole_imgs", help="Input image or folder. Default: inputs/whole_imgs"
    )
    parser.add_argument("-o", "--output", type=str, default="results", help="Output folder. Default: results")
    # we use version to select models, which is more user-friendly
    parser.add_argument("--img_size", type=int, default=96, help="size to reshape the detected face")
    parser.add_argument(
        "-v",
        "--version",
        type=str,
        default="1.4",
        help="GFPGAN model version. Option: 1 | 1.2 | 1.3 | 1.4. Default: 1.4",
    )
    parser.add_argument(
        "-s", "--upscale", type=int, default=2, help="The final upsampling scale of the image. Default: 2"
    )
    parser.add_argument(
        "--bg_upsampler", type=str, default="realesrgan", help="background upsampler. Default: realesrgan"
    )
    parser.add_argument(
        "--bg_tile",
        type=int,
        default=400,
        help="Tile size for background sampler, 0 for no tile during testing. Default: 400",
    )
    parser.add_argument("--suffix", type=str, default=None, help="Suffix of the restored faces")
    parser.add_argument("--only_center_face", action="store_true", help="Only restore the center face")
    parser.add_argument("--aligned", action="store_true", help="Input are aligned faces")
    parser.add_argument("--save_faces", default=False, help="Save the restored faces")
    parser.add_argument(
        "--ext",
        type=str,
        default="auto",
        help="Image extension. Options: auto | jpg | png, auto means using the same extension as inputs. Default: auto",
    )
    args = parser.parse_args()

    if os.path.isfile(args.face) and args.face.split(".")[1] in ["jpg", "png", "jpeg"]:
        args.static = True
    os.makedirs(args.output, exist_ok=True)

    return args


# %% Custom functions
def get_smoothened_boxes(boxes, T):
    for i in range(len(boxes)):
        if i + T > len(boxes):
            window = boxes[len(boxes) - T :]
        else:
            window = boxes[i : i + T]
        boxes[i] = np.mean(window, axis=0)
    return boxes


def face_detect(args, images):
    detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, flip_input=False, device=args.device)

    batch_size = args.face_det_batch_size

    while 1:
        predictions = []
        try:
            with torch.no_grad():
                for i in tqdm(range(0, len(images), batch_size)):
                    with torch.autocast(device_type=args.device, dtype=torch.bfloat16):
                        predictions.extend(detector.get_detections_for_batch(np.array(images[i : i + batch_size])))
        except RuntimeError:
            if batch_size == 1:
                raise RuntimeError(
                    "Image too big to run face detection on GPU. Please use the --resize_factor argument"
                )
            batch_size //= 2
            print("Recovering from OOM error; New batch size: {}".format(batch_size))
            continue
        break

    results = []
    pady1, pady2, padx1, padx2 = args.pads
    for rect, image in zip(predictions, images):
        if rect is None:
            cv2.imwrite("temp/faulty_frame.jpg", image)  # check this frame where the face was not detected.
            raise ValueError("Face not detected! Ensure the video contains a face in all the frames.")

        y1 = max(0, rect[1] - pady1)
        y2 = min(image.shape[0], rect[3] + pady2)
        x1 = max(0, rect[0] - padx1)
        x2 = min(image.shape[1], rect[2] + padx2)

        results.append([x1, y1, x2, y2])

    boxes = np.array(results)
    if not args.nosmooth:
        boxes = get_smoothened_boxes(boxes, T=5)
    results = [[image[y1:y2, x1:x2], (y1, y2, x1, x2)] for image, (x1, y1, x2, y2) in zip(images, boxes)]

    del detector
    return results


def datagen(args, frames, mels):
    img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

    if args.box[0] == -1:
        if not args.static:
            face_det_results = face_detect(args, frames)  # BGR2RGB for CNN face detection
        else:
            face_det_results = face_detect(args, [frames[0]])
    else:
        print("Using the specified bounding box instead of face detection...")
        y1, y2, x1, x2 = args.box
        face_det_results = [[f[y1:y2, x1:x2], (y1, y2, x1, x2)] for f in frames]

    for i, m in enumerate(mels):
        idx = 0 if args.static else i % len(frames)
        frame_to_save = frames[idx].copy()
        face, coords = face_det_results[idx].copy()

        face = cv2.resize(face, (args.img_size, args.img_size))

        img_batch.append(face)
        mel_batch.append(m)
        frame_batch.append(frame_to_save)
        coords_batch.append(coords)

        if len(img_batch) >= args.wav2lip_batch_size:
            img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

            img_masked = img_batch.copy()
            img_masked[:, args.img_size // 2 :] = 0

            img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.0
            mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

            yield img_batch, mel_batch, frame_batch, coords_batch
            img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

    if len(img_batch) > 0:
        img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

        img_masked = img_batch.copy()
        img_masked[:, args.img_size // 2 :] = 0

        img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.0
        mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

        yield img_batch, mel_batch, frame_batch, coords_batch


def _load(args):
    if args.device == "cuda":
        checkpoint = torch.load(args.checkpoint_path)
    else:
        checkpoint = torch.load(args.checkpoint_path, map_location=lambda storage, loc: storage)
    return checkpoint


def load_model(args):
    model = Wav2Lip()
    print("Load checkpoint from: {}".format(args.checkpoint_path))
    checkpoint = _load(args)
    s = checkpoint["state_dict"]
    new_s = {}
    for k, v in s.items():
        new_s[k.replace("module.", "")] = v
    model.load_state_dict(new_s)
    return model.eval().to(args.device)


def load_bg_upsampler(args):
    # if (not torch.cuda.is_available()) or (not hthpu.is_available()):  # CPU
    if args.device == "cpu":
        import warnings

        warnings.warn(
            "The unoptimized RealESRGAN is slow on CPU. We do not use it. "
            "If you really want to use it, please modify the corresponding codes."
        )
        bg_upsampler = None
    else:
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        bg_upsampler = RealESRGANer(
            scale=2,
            model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
            model=model,
            tile=args.bg_tile,
            tile_pad=10,
            pre_pad=0,
            half=True,
        )  # need to set False in CPU mode
    return bg_upsampler.eval().to(args.device)


def load_gfpgan(args, bg_upsampler):
    if args.version == "1":
        arch = "original"
        channel_multiplier = 1
        model_name = "GFPGANv1"
    elif args.version == "1.2":
        arch = "clean"
        channel_multiplier = 2
        model_name = "GFPGANCleanv1-NoCE-C2"
    elif args.version == "1.3":
        arch = "clean"
        channel_multiplier = 2
        model_name = "GFPGANv1.3"
    elif args.version == "1.4":
        arch = "clean"
        channel_multiplier = 2
        model_name = "GFPGANv1.4"
    else:
        raise ValueError(f"Wrong model version {args.version}.")

    # determine model path
    pythonpath = os.environ.get("PYTHONPATH").split(":")[0]
    model_path = path.join(pythonpath, "gfpgan/experiments/pretrained_models", model_name + ".pth")
    if not path.isfile(model_path):
        model_path = path.join(pythonpath, "gfpgan/realesrgan/weights", model_name + ".pth")
    if not path.isfile(model_path):
        raise ValueError(f"Model {model_name} does not exist")

    restorer = GFPGANer(
        model_path=model_path,
        upscale=args.upscale,
        arch=arch,
        channel_multiplier=channel_multiplier,
        bg_upsampler=bg_upsampler,
        device=args.device,
    )

    # Optional: torch.compile

    return restorer


def base64_to_int16_to_wav(base64_string, output_wav_file):
    """Convert base64 string to int16 numpy array and save as .wav file."""
    # Decode the base64 string to binary data
    wav_bytes = base64.b64decode(base64_string)

    # Read the binary data using soundfile
    buf = io.BytesIO(wav_bytes)
    y, sr = sf.read(buf, dtype="int16")

    # Write the binary data to a .wav file
    sf.write(output_wav_file, y, sr, format="WAV")
    return sr, y
