

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# SCRIPT USAGE NOTICE:  By downloading and using any script file included
# with the associated software package (such as files with .bat, .cmd, or 
# .JS extensions, Docker files, or any other type of file that, when executed,
# automatically downloads and/or installs files onto your system) (the “Script File”),
# it is your obligation to review the Script File to understand what files (e.g.,
# other software, AI models, AI Datasets) the Script File will download to your system
# (“Downloaded Files”). Furthermore, by downloading and using the Downloaded Files,
# even if they are installed through a silent install, you agree to any and all
# terms and conditions associated with such files, including but not limited to,
# license terms, notices, or disclaimers.


# HABANA environment
FROM vault.habana.ai/gaudi-docker/1.14.0/ubuntu22.04/habanalabs/pytorch-installer-2.1.1 AS hpu
RUN rm -rf /etc/ssh/ssh_host*

# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/home/user:/usr/lib/habanalabs/:/optimum-habana

# Install required branch
RUN git clone https://github.com/lkk12014402/optimum-habana.git /optimum-habana -b enable_llava_generation

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY requirements.txt /tmp/requirements.txt

# Install dependency
RUN pip install --no-cache-dir -U -r /tmp/requirements.txt

# work dir should contains the server
WORKDIR /llava_server
COPY llava_server /llava_server

ENTRYPOINT ["python", "llava_server.py"]
