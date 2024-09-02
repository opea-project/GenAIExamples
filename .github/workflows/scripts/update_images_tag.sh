#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

declare -A dict
dict["ghcr.io/huggingface/text-generation-inference"]="docker://ghcr.io/huggingface/text-generation-inference:latest-intel-cpu"

function get_latest_version() {
    repo_image=$1
    if [[ $repo_image == *"huggingface"* ]]; then
        revision=$(skopeo inspect --config ${dict[$repo_image]} | jq -r '.config.Labels["org.opencontainers.image.revision"][:7]')
        latest_version="sha-$revision-intel-cpu"
    else
        versions=$(skopeo list-tags ${dict[$repo_image]} | jq -r '.Tags[]')
        printf "version list:\n$versions\n"
        latest_version=$(printf "%s\n" "${versions[@]}" | grep -E '^[\.0-9\-]+$' | sort -V | tail -n 1)
    fi
    echo "latest version: $latest_version"
    replace_image_version $repo_image $latest_version
}

function replace_image_version() {
    repo_image=$1
    version=$2
    if [[ -z "$version" ]]; then
        echo "version is empty"
    else
        echo "replace $repo_image:tag with $repo_image:$version"
        find . -name "Dockerfile" | xargs sed -i "s|$repo_image:sha[A-Za-z0-9\-]*|$repo_image:$version|g"
        find . -name "*.yaml" | xargs sed -i "s|$repo_image:sha[A-Za-z0-9\-]*|$repo_image:$version|g"
        find . -name "*.md" | xargs sed -i "s|$repo_image:sha[A-Za-z0-9\-]*|$repo_image:$version|g"
    fi
}

function main() {
    for repo_image in "${!dict[@]}"; do
        echo "::group::check $repo_image"
        get_latest_version $repo_image
        echo "::endgroup::"
    done
}

main
