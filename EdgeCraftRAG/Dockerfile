FROM python:3.11-slim

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev 

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

COPY ./edgecraftrag /home/user/edgecraftrag
COPY ./chatqna.py /home/user/chatqna.py

WORKDIR /home/user/edgecraftrag
RUN pip install -r requirements.txt

WORKDIR /home/user

USER user

RUN echo 'ulimit -S -n 999999' >> ~/.bashrc

ENTRYPOINT ["python", "chatqna.py"]