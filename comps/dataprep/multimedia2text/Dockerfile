# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use the official Python 3.11 slim image as the base image
FROM python:3.11-slim

# Set environment variables
ENV LANG=C.UTF-8

# Install necessary packages and clean up to reduce image size
RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a directory for the user and set it as the working directory
WORKDIR /home/user

# Copy the application code and requirements file to the container
COPY comps /home/user/comps
COPY requirements.txt /home/user/requirements.txt
COPY ./comps/dataprep/multimedia2text/multimedia2text.py /home/user/multimedia2text.py

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt 

# Define the entry point for the container
ENTRYPOINT ["python", "multimedia2text.py"]
