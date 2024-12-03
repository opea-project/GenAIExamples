# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os.path
import subprocess
import sys

import yaml

images = {}


def check_docker_compose_build_definition(file_path):
    with open(file_path, "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for service in data["services"]:
            if "build" in data["services"][service] and "image" in data["services"][service]:
                bash_command = "echo " + data["services"][service]["image"]
                image = (
                    subprocess.run(["bash", "-c", bash_command], check=True, capture_output=True)
                    .stdout.decode("utf-8")
                    .strip()
                )
                build = data["services"][service]["build"]
                context = build.get("context", "")
                dockerfile = os.path.normpath(
                    os.path.join(os.path.dirname(file_path), context, build.get("dockerfile", ""))
                )
                if not os.path.isfile(dockerfile):
                    # dockerfile not exists in the current repo context, assume it's in 3rd party context
                    dockerfile = os.path.normpath(os.path.join(context, build.get("dockerfile", "")))
                item = {"file_path": file_path, "service": service, "dockerfile": dockerfile}
                if image in images and dockerfile != images[image]["dockerfile"]:
                    print("ERROR: !!! Found Conflicts !!!")
                    print(f"Image: {image}, Dockerfile: {dockerfile}, defined in Service: {service}, File: {file_path}")
                    print(
                        f"Image: {image}, Dockerfile: {images[image]['dockerfile']}, defined in Service: {images[image]['service']}, File: {images[image]['file_path']}"
                    )
                    sys.exit(1)
                else:
                    # print(f"Add Image: {image} Dockerfile: {dockerfile}")
                    images[image] = item


def parse_arg():
    parser = argparse.ArgumentParser(
        description="Check for conflicts in image build definition in docker-compose.yml files"
    )
    parser.add_argument("files", nargs="+", help="list of files to be checked")
    return parser.parse_args()


def main():
    args = parse_arg()
    for file_path in args.files:
        check_docker_compose_build_definition(file_path)
    print("SUCCESS: No Conlicts Found.")
    return 0


if __name__ == "__main__":
    main()
