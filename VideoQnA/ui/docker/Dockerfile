# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir streamlit

COPY ui.py /app/ui.py

EXPOSE 5173

HEALTHCHECK CMD curl --fail http://localhost:5173/_stcore/health

ENTRYPOINT ["streamlit", "run", "ui.py", "--server.port=5173", "--server.address=0.0.0.0"]
