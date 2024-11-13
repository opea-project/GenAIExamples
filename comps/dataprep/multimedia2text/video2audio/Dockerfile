# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use the official Python 3.11 slim image as the base image
FROM python:3.11-slim

# Set environment variables
ENV LANG=C.UTF-8

# Install necessary packages
RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev 

# Create a directory for the user
RUN mkdir -p /home/user

# Copy the application code to the container
COPY comps /home/user/comps
COPY requirements.txt /home/user/requirements.txt
COPY ./comps/dataprep/multimedia2text/video2audio/video2audio_microservice.py /home/user/video2audio_microservice.py

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r /home/user/requirements.txt moviepy

# Set the working directory
WORKDIR /home/user/

# Define the entry point for the container
ENTRYPOINT ["python", "video2audio_microservice.py"]
