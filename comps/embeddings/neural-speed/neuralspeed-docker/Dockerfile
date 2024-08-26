# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

From ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

ENV GLIBC_TUNABLES glibc.cpu.x86_shstk=permissive

COPY comps /root/comps
COPY neural_speed-0.1.dev117+gafc0030.d20240815-cp310-cp310-linux_x86_64.whl /root/
COPY bge-base-q8.bin /root/

RUN apt update && apt install -y python3 python3-pip 
RUN pip3 install -r /root/comps/embeddings/neural-speed/neuralspeed-docker/requirements.txt
RUN pip3 install llmspec mosec msgspec httpx requests
RUN pip3 install /root/neural_speed-0.1.dev117+gafc0030.d20240815-cp310-cp310-linux_x86_64.whl

RUN cd /root/ && export HF_ENDPOINT=https://hf-mirror.com && huggingface-cli download --resume-download BAAI/bge-base-en-v1.5 --local-dir /root/bge-base-en-v1.5


ENV LD_PRELOAD=/root/libstdc++.so.6


WORKDIR /root/comps/embeddings/neural-speed/neuralspeed-docker

CMD ["python3", "server.py"]
