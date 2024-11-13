# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use the official Python 3.11 slim image as the base image
FROM python:3.11-slim

# Create a new user and set up the home directory
RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/
USER user

# Set environment variables
ENV LANG=C.UTF-8
ARG ARCH=cpu

# Copy the application code and requirements file to the container
COPY comps /home/user/comps
COPY requirements.txt /home/user/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    if [ "${ARCH}" = "cpu" ]; then \
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
        pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /home/user/requirements.txt ; \
    else \
        pip install --no-cache-dir -r /home/user/requirements.txt ; \
    fi

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=$PYTHONPATH:/home/user

# Set the working directory
WORKDIR /home/user/comps/dataprep/multimedia2text/audio2text

# Define the entry point for the container
ENTRYPOINT ["python", "audio2text.py"]
