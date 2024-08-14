# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:22.04

ARG TAG=main

RUN apt-get update \ 
    && apt-get upgrade -y \ 
    && apt-get install -y --no-install-recommends \
    gcc-12 \
    g++-12 \
    make \
    wget \
    libnuma-dev \
    numactl \
    git \
    pkg-config \
    software-properties-common \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    libbz2-dev \
    libsqlite3-dev \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 60 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 60 \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install python
WORKDIR /tmp
RUN wget -q https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz \
    && tar -xzvf Python-3.8.10.tgz
WORKDIR /tmp/Python-3.8.10
RUN ./configure --prefix=/usr/bin/python3.8 --enable-optimizations \
    && make -j \
    && make install \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.8/bin/python3.8 60 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/python3.8/bin/pip3 60 \
    && python -m pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir wheel \
    && rm -rf /tmp/* \
    && echo "export PATH=/usr/bin/python3.8:\$PATH" >> ~/.bashrc

RUN pip install --no-cache-dir torch==2.3.0+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir cmake==3.26.1 transformers==4.41.2 sentencepiece==0.1.99 accelerate==0.23.0 protobuf tiktoken transformers-stream-generator einops \
    && ln -s /usr/bin/python3.8/lib/python3.8/site-packages/cmake/data/bin/cmake /usr/bin/cmake

# Install oneCCL
RUN git clone https://github.com/oneapi-src/oneCCL.git /tmp/oneCCL
WORKDIR /tmp/oneCCL
RUN git checkout 2021.10 \
    && sed -i 's/cpu_gpu_dpcpp/./g' cmake/templates/oneCCLConfig.cmake.in \
    && mkdir build
WORKDIR /tmp/oneCCL/build
RUN cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/oneCCL \
    && make -j install

RUN echo "source /usr/local/oneCCL/env/setvars.sh" >> ~/.bashrc

WORKDIR /home/user/
RUN rm -rf /tmp/oneCCL

RUN git clone https://github.com/intel/xFasterTransformer.git

SHELL ["/bin/bash", "-c"]
WORKDIR /home/user/xFasterTransformer
RUN git checkout ${TAG} \
    && export "LD_LIBRARY_PATH=/usr/local/mklml_lnx_2019.0.5.20190502/lib:$LD_LIBRARY_PATH" \
    && export "PATH=/usr/bin/python3.8:$PATH" \
    && echo "source /usr/local/oneCCL/env/setvars.sh" >> ~/.bash_profile \
    && source ~/.bash_profile \
    && python setup.py build \
    && python setup.py egg_info bdist_wheel --verbose \
    && pip install --no-cache-dir dist/*

RUN mkdir -p /usr/local/xft/lib \
    && cp /home/user/xFasterTransformer/build/libxfastertransformer.so /usr/local/xft/lib \
    && cp /home/user/xFasterTransformer/build/libxft_comm_helper.so /usr/local/xft/lib \
    && cp -r /home/user/xFasterTransformer/include /usr/local/xft/ \
    && mkdir -p  /usr/local/include/xft/ \
    && ln -s /usr/local/xft/include /usr/local/include/xft/include

RUN echo "export \$(python -c 'import xfastertransformer as xft; print(xft.get_env())')" >> ~/.bashrc

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/llms/text-generation/vllm-xft/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/root

RUN chmod +x /home/user/comps/llms/text-generation/vllm-xft/run.sh

WORKDIR /home/user/comps/llms/text-generation/vllm-xft/

ENTRYPOINT ["/home/user/comps/llms/text-generation/vllm-xft/run.sh"]
