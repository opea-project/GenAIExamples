FROM python:3.11-slim

ENV LANG C.UTF-8

# Install system dependencies
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get install -y curl \
    && apt-get install -y libomp-dev google-perftools

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/comps/tts/requirements.txt && \
    pip install --no-cache-dir -r /home/comps/cores/telemetry/requirements.txt

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libiomp5.so:/usr/lib/x86_64-linux-gnu/libtcmalloc.so.4
ENV MALLOC_CONF="oversize_threshold:1,background_thread:true,metadata_thp:auto,dirty_decay_ms:9000000000,muzzy_decay_ms:9000000000"
ENV OMP_NUM_THREADS=56

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/tts

ENTRYPOINT ["python", "tts.py"]