#!/usr/bin/env bash
set -e

git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps

docker build -t opea/llm-faqgen-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/faq-generation/tgi/Dockerfile .
docker save -o "llm-faqgen-tgi-latest.tar"  opea/llm-faqgen-tgi:latest 
sudo nerdctl -n k8s.io load -i "llm-faqgen-tgi-latest.tar"

cd ..


git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/FaqGen/docker/

docker build --no-cache -t opea/faqgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
docker save -o "faqgen-latest.tar"  opea/faqgen:latest
sudo nerdctl -n k8s.io load -i "faqgen-latest.tar"

cd ui
docker build -t opea/faqgen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
docker save -o "faqgen-ui-latest.tar"  opea/faqgen-ui:latest
sudo nerdctl -n k8s.io load -i "faqgen-ui-latest.tar"
