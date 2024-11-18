#!/bin/sh

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Check the value of $DEVICE and cd to the download path accordingly
if [ "$DEVICE" = "hpu" ]; then
    cd /usr/local/lib/python3.10/dist-packages
else
    cd /usr/local/lib/python3.11/site-packages
fi

# Download model weights
wget --no-verbose https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth -O Wav2Lip/face_detection/detection/sfd/s3fd.pth
mkdir -p Wav2Lip/checkpoints
wget --no-verbose "https://iiitaphyd-my.sharepoint.com/:f:/g/personal/radrabha_m_research_iiit_ac_in/Eb3LEzbfuKlJiR600lQWRxgBIY27JZg80f7V9jtMfbNDaQ?download=1" -O Wav2Lip/checkpoints/wav2lip.pth
wget --no-verbose "https://iiitaphyd-my.sharepoint.com/:f:/g/personal/radrabha_m_research_iiit_ac_in/EdjI7bZlgApMqsVoEUUXpLsBxqXbn5z8VTmoxp55YNDcIA?download=1" -O Wav2Lip/checkpoints/wav2lip_gan.pth
wget --no-verbose https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth -P gfpgan/experiments/pretrained_models
echo "Face Detector, Wav2Lip, GFPGAN weights downloaded."

# Environment variables
export PT_HPU_LAZY_MODE=0
export PT_HPU_ENABLE_REFINE_DYNAMIC_SHAPES=1

# Wav2Lip, GFPGAN
cd /home/user/comps/animation/wav2lip/ || exit
python3 dependency/wav2lip_server.py \
--device $DEVICE \
--port $((WAV2LIP_PORT)) \
--inference_mode $INFERENCE_MODE \
--checkpoint_path $CHECKPOINT_PATH \
--face $FACE \
--audio $AUDIO \
--outfile $OUTFILE \
--img_size $((FACESIZE)) \
-v $GFPGAN_MODEL_VERSION \
-s $((UPSCALE_FACTOR)) \
--fps $((FPS)) \
--only_center_face \
--bg_upsampler None
