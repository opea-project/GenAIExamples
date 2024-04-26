# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

FROM langchain/langchain:latest

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev

# RUN useradd -m -s /bin/bash user && \
#     mkdir -p /home/user && \
#     chown -R user /home/user/

# USER user

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/ws:/home/user:/home/user/qna-app/app

WORKDIR /home/user/qna-app
COPY qna-app /home/user/qna-app

ENTRYPOINT ["/usr/bin/sleep", "infinity"]
