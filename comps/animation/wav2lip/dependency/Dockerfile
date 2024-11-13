# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use a base image
FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages:/home:/home/user
ENV PYTHON=/usr/bin/python3.11

# Install dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    yasm \
    build-essential \
    pkg-config \
    libx264-dev \
    git \
    nasm \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install GenAIComps
RUN mkdir -p /home/user/comps
COPY comps /home/user/comps
COPY comps/animation/wav2lip/dependency/entrypoint.sh /usr/local/bin/entrypoint.sh

# Install ffmpeg with x264 software codec
RUN git clone https://github.com/FFmpeg/FFmpeg.git /home/user/comps/animation/wav2lip/FFmpeg
WORKDIR /home/user/comps/animation/wav2lip/FFmpeg
RUN ./configure --enable-gpl --enable-libx264 --enable-cross-compile && \
    make -j$(nproc-1) && \
    make install && \
    hash -r
RUN chmod +x $(which ffmpeg)

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Install Wav2Lip from pip
RUN pip install --no-deps Wav2Lipy
RUN rm /usr/local/lib/python3.11/site-packages/Wav2Lip/__init__.py && touch /usr/local/lib/python3.11/site-packages/Wav2Lip/__init__.py
ENV PYTHONPATH="$PYTHONPATH:/usr/local/lib/python3.11/site-packages/Wav2Lip"

# Install GFPGAN from pip
RUN pip install --no-deps gfpgan
RUN touch /usr/local/lib/python3.11/site-packages/gfpgan/__init__.py
ENV PYTHONPATH="$PYTHONPATH:/usr/local/lib/python3.11/site-packages/gfpgan"

# Download pre-trained models
WORKDIR /usr/local/lib/python3.11/site-packages

# Install pip dependencies
RUN pip install -r /home/user/comps/animation/wav2lip/requirements.txt

# Custom patches
# Modify the degradations.py file to import rgb_to_grayscale from torchvision.transforms.functional
RUN sed -i 's/from torchvision.transforms.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' /usr/local/lib/python3.11/site-packages/basicsr/data/degradations.py

# Modify the core.py file to include 'hpu' in the device check
RUN sed -i "s/if 'cpu' not in device and 'cuda' not in device:/if 'cpu' not in device and 'cuda' not in device and 'hpu' not in device:/" /usr/local/lib/python3.11/site-packages/Wav2Lip/face_detection/detection/core.py

# To be compatible with librosa==0.10.2, instead of librosa==0.7.0 because the co-dependency numba==0.48 cannot be pip installed
RUN sed -i 's/hp.sample_rate, hp.n_fft/sr=hp.sample_rate, n_fft=hp.n_fft/' /usr/local/lib/python3.11/site-packages/Wav2Lip/audio.py

# Set the working directory
WORKDIR /home/user/comps/animation/wav2lip/

# Define the command to run when the container starts
RUN chmod +x /usr/local/bin/entrypoint.sh
ENV DEVICE="cpu"
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
