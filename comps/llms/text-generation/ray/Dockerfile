FROM vault.habana.ai/gaudi-docker/1.15.1/ubuntu22.04/habanalabs/pytorch-installer-2.2.0:latest

ENV LANG=en_US.UTF-8

WORKDIR /root/rayllm

# copy the source code to the package directory
COPY ../ray/ /root/rayllm

RUN pip install -r /root/rayllm/docker/requirements.txt && \
    pip install --upgrade-strategy eager optimum[habana]

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    service ssh restart

ENV no_proxy=localhost,127.0.0.1
ENV PYTHONPATH=$PYTHONPATH:/root:/root/rayllm

# Required by DeepSpeed
ENV RAY_EXPERIMENTAL_NOSET_HABANA_VISIBLE_MODULES=1

ENV PT_HPU_LAZY_ACC_PAR_MODE=0

ENV PT_HPU_ENABLE_REFINE_DYNAMIC_SHAPES=0

ENV PT_HPU_ENABLE_WEIGHT_CPU_PERMUTE=0

ENV PT_HPU_ENABLE_LAZY_COLLECTIVES=true