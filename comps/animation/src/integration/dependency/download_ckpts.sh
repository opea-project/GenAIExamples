# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

wget https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth -O Wav2Lip/face_detection/detection/sfd/s3fd.pth
mkdir -p Wav2Lip/checkpoints
wget "https://iiitaphyd-my.sharepoint.com/:f:/g/personal/radrabha_m_research_iiit_ac_in/Eb3LEzbfuKlJiR600lQWRxgBIY27JZg80f7V9jtMfbNDaQ?download=1" -O Wav2Lip/checkpoints/wav2lip.pth
wget "https://iiitaphyd-my.sharepoint.com/:f:/g/personal/radrabha_m_research_iiit_ac_in/EdjI7bZlgApMqsVoEUUXpLsBxqXbn5z8VTmoxp55YNDcIA?download=1" -O Wav2Lip/checkpoints/wav2lip_gan.pth
wget https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth -P gfpgan/experiments/pretrained_models
