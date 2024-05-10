FROM python:3.11-slim

ENV LANG C.UTF-8

# Install system dependencies
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get install -y curl

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/comps/tts/requirements.txt && \
    pip install --no-cache-dir -r /home/comps/cores/telemetry/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/tts

ENTRYPOINT ["python", "tts.py"]