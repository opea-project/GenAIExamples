# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM vault.habana.ai/gaudi-docker/1.18.0/ubuntu22.04/habanalabs/pytorch-installer-2.4.0 AS hpu

ENV LANG=en_US.UTF-8

WORKDIR /home/user/vllm/ray

# copy the source code to the package directory
COPY comps/llms/text-generation/vllm/ray /home/user/vllm/ray

RUN pip install --no-cache-dir --upgrade-strategy eager optimum[habana] && \
    pip install --no-cache-dir git+https://github.com/HabanaAI/DeepSpeed.git@1.15.1
RUN pip install --no-cache-dir -v git+https://github.com/HabanaAI/vllm-fork.git@cf6952d
RUN pip install --no-cache-dir "ray>=2.10" "ray[serve,tune]>=2.10"

RUN ssh-keygen -A && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    service ssh restart

ENV PYTHONPATH=$PYTHONPATH:/root:/home/user/vllm/ray

# Required by DeepSpeed
ENV RAY_EXPERIMENTAL_NOSET_HABANA_VISIBLE_MODULES=1

ENV PT_HPU_LAZY_ACC_PAR_MODE=0

ENV PT_HPU_ENABLE_LAZY_COLLECTIVES=true
