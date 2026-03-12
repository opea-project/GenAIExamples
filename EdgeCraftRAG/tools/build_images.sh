#!/usr/bin/env bash
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${PROJECT_DIR}"

build_mega() {
  echo "Building opea/edgecraftrag:latest"
  docker build --no-cache --pull \
    --build-arg http_proxy="${http_proxy-}" \
    --build-arg https_proxy="${https_proxy-}" \
    --build-arg no_proxy="${no_proxy-}" \
    -t opea/edgecraftrag:latest \
    -f Dockerfile .
}

build_server() {
  echo "Building opea/edgecraftrag-server:latest"
  docker build --no-cache --pull \
    --build-arg http_proxy="${http_proxy-}" \
    --build-arg https_proxy="${https_proxy-}" \
    --build-arg no_proxy="${no_proxy-}" \
    -t opea/edgecraftrag-server:latest \
    -f Dockerfile.server .
}

build_ui() {
  echo "Building opea/edgecraftrag-ui:latest"
  docker build --no-cache --pull \
    --build-arg http_proxy="${http_proxy-}" \
    --build-arg https_proxy="${https_proxy-}" \
    --build-arg no_proxy="${no_proxy-}" \
    -t opea/edgecraftrag-ui:latest \
    -f ui/docker/Dockerfile.ui .
}

print_usage() {
  echo "Usage: ./tools/build_images.sh [mega|server|ui|all] ..."
  echo "Examples:"
  echo "  ./tools/build_images.sh"
  echo "  ./tools/build_images.sh ui"
  echo "  ./tools/build_images.sh mega server"
}

if [ "$#" -eq 0 ]; then
  build_mega
  build_server
  build_ui
  echo "All images built successfully."
  exit 0
fi

for target in "$@"; do
  case "$target" in
    mega)
      build_mega
      ;;
    server)
      build_server
      ;;
    ui)
      build_ui
      ;;
    all)
      build_mega
      build_server
      build_ui
      ;;
    -h|--help|help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown target: $target"
      print_usage
      exit 1
      ;;
  esac
done

echo "Requested image build(s) completed successfully."
