

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

FROM intel/intel-optimized-pytorch:2.2.0-pip-jupyter

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

ENV PYTHONPATH=/home/user:/home/user/summarize-app/app

WORKDIR /home/user/summarize-app
COPY summarize-app /home/user/summarize-app
