FROM langchain/langchain:latest

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

ENV PYTHONPATH=/home/user:/home/user/summarize-app/app

WORKDIR /home/user/summarize-app
COPY summarize-app /home/user/summarize-app
