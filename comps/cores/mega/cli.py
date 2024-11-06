# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse

from .exporter import convert_to_docker_compose
from .manifests_exporter import convert_to_manifests


def export_kubernetes_manifests(mega_yaml, output_file):
    print(f"Generating Kubernetes manifests from {mega_yaml} to {output_file}")
    convert_to_manifests(mega_yaml, output_file)


def export_docker_compose(mega_yaml, output_file):
    print(f"Generating Docker Compose file from {mega_yaml} to {output_file}")
    convert_to_docker_compose(mega_yaml, output_file)


def opea_execute():
    parser = argparse.ArgumentParser(description="OPEA CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="commands")

    # Subcommand for export
    export_parser = subparsers.add_parser("export", help="Export resources")

    # Subparsers for export to docker-compose and kubernetes
    export_subparsers = export_parser.add_subparsers(dest="export_command", help="Export commands")

    # Export to Docker Compose
    compose_parser = export_subparsers.add_parser("docker-compose", help="Export to Docker Compose")
    compose_parser.add_argument("mega_yaml", help="Path to the mega YAML file")
    compose_parser.add_argument("output_file", help="Path to the Docker Compose file")

    # Export to Kubernetes
    kube_parser = export_subparsers.add_parser("kubernetes", help="Export to Kubernetes")
    kube_parser.add_argument("mega_yaml", help="Path to the mega YAML file")
    kube_parser.add_argument("output_dir", help="Directory to store generated Kubernetes manifests")
    kube_parser.add_argument(
        "--device", choices=["cpu", "gaudi", "xpu", "gpu"], default="cpu", help="Device type to use (default: cpu)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Execute appropriate command
    if args.command == "export":
        if args.export_command == "docker-compose":
            export_docker_compose(args.mega_yaml, args.output_file)
        elif args.export_command == "kubernetes":
            export_kubernetes_manifests(args.mega_yaml, args.output_dir, args.device)
        else:
            parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    opea_execute()
