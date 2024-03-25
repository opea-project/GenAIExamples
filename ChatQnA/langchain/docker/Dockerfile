FROM langchain/langchain

ARG http_proxy
ARG https_proxy
ENV http_proxy=$http_proxy
ENV https_proxy=$https_proxy

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        libgl1-mesa-glx \
        libjemalloc-dev

RUN pip install --upgrade pip \
    sentence-transformers \
    redis \
    unstructured \
    unstructured[all-docs] \
    langchain-cli \
    pydantic==1.10.13 \
    langchain==0.1.12 \
    poetry \
    pymupdf \
    easyocr \
    langchain_benchmarks \
    pyarrow \
    jupyter \
    intel-extension-for-pytorch \
    intel-openmp

ENV PYTHONPATH=/ws:/qna-app/app

COPY qna-app /qna-app
WORKDIR /qna-app

ENTRYPOINT ["/usr/bin/sleep", "infinity"]
