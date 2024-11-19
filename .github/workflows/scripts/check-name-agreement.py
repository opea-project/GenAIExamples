# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse

from ruamel.yaml import YAML


def parse_yaml_file(file_path):
    yaml = YAML()
    with open(file_path, "r") as file:
        data = yaml.load(file)
    return data


def check_service_image_consistency(data):
    inconsistencies = []
    for service_name, service_details in data.get("services", {}).items():
        image_name = service_details.get("image", "")
        # Extract the image name part after the last '/'
        image_name_part = image_name.split("/")[-1].split(":")[0]
        # Check if the service name is a substring of the image name part
        if service_name not in image_name_part:
            # Get the line number of the service name
            line_number = service_details.lc.line + 1
            inconsistencies.append((service_name, image_name, line_number))
    return inconsistencies


def main():
    parser = argparse.ArgumentParser(description="Check service name and image name consistency in a YAML file.")
    parser.add_argument("file_path", type=str, help="The path to the YAML file.")
    args = parser.parse_args()

    data = parse_yaml_file(args.file_path)

    inconsistencies = check_service_image_consistency(data)
    if inconsistencies:
        for service_name, image_name, line_number in inconsistencies:
            print(f"Service name: {service_name}, Image name: {image_name}, Line number: {line_number}")
    else:
        print("All consistent")


if __name__ == "__main__":
    main()
