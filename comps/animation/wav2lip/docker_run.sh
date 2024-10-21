# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

docker run --privileged --rm -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker -v $(pwd):$(pwd) -w /home/user/comps/animation -it --runtime=habana -e HABANA_VISIBLE_DEVICES="3" -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PYTHON=/usr/bin/python3.10 -e INFERNCE_MODE=$INFERNCE_MODE -e CHECKPOINT_PATH=$CHECKPOINT_PATH -e FACE=$FACE -e AUDIO=$AUDIO -e FACESIZE=$FACESIZE -e OUTFILE=$OUTFILE -e GFPGAN_MODEL_VERSION=$GFPGAN_MODEL_VERSION -e UPSCALE_FACTOR=$UPSCALE_FACTOR -e FPS=$FPS --cap-add=sys_nice --net=host --ipc=host opea/animation:test
