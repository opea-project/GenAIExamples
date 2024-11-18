# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
#To anounce the version of the codes, please create a version.txt and have following format.
#VERSION_MAJOR 1
#VERSION_MINOR 0
#VERSION_PATCH 0

VERSION_FILE="version.txt"
if [ -f $VERSION_FILE ]; then
    VER_OPEA_MAJOR=$(grep "VERSION_MAJOR" $VERSION_FILE | cut -d " " -f 2)
    VER_OPEA_MINOR=$(grep "VERSION_MINOR" $VERSION_FILE | cut -d " " -f 2)
    VER_OPEA_PATCH=$(grep "VERSION_PATCH" $VERSION_FILE | cut -d " " -f 2)
    export TAG=$VER_OPEA_MAJOR.$VER_OPEA_MINOR
    echo OPEA Version:$TAG
fi
