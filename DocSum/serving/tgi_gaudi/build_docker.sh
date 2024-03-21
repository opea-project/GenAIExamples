#!/bin/bash

git clone https://github.com/huggingface/tgi-gaudi.git
cd ./tgi-gaudi/
docker build -t tgi_gaudi_doc_summary . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
