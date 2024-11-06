# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import unittest

import yaml

from comps.cores.mega.exporter import convert_to_docker_compose


class TestConvertToDockerCompose(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        # Paths for the `mega.yaml` and output file
        self.mega_yaml = os.path.join(self.test_dir, "mega.yaml")
        self.output_file = os.path.join(self.test_dir, "docker-compose.yaml")

    def tearDown(self):
        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)

    def test_convert_to_docker_compose(self):
        # Call the function directly
        convert_to_docker_compose(self.mega_yaml, self.output_file)

        # Load and verify the content of the generated docker-compose.yaml
        with open(self.output_file, "r") as f:
            docker_compose = yaml.safe_load(f)

        self.assertEqual(docker_compose["version"], "3.8")
        self.assertIn("services", docker_compose)
        self.assertIn("redis-vector-db", docker_compose["services"])
        self.assertIn("llm-server", docker_compose["services"])
        self.assertEqual(
            docker_compose["services"]["llm-server"]["image"],
            "ghcr.io/huggingface/tgi-gaudi:2.0.5",
        )

    # def test_convert_to_docker_compose_cli(self):
    #     # Define shell command
    #     command = ["opea", "export", "docker-compose", self.mega_yaml, self.output_file, "--device=cpu"]

    #     # Run the CLI command
    #     result = subprocess.run(command, capture_output=True, text=True)

    #     # Check for command success
    #     self.assertEqual(result.returncode, 0, f"Command failed with error: {result.stderr}")

    #     # Verify the output file
    #     if os.path.isfile(self.output_file):
    #         print("Docker Compose file generated successfully.")

    #         # Check for key properties in the docker-compose file
    #         with open(self.output_file, "r") as f:
    #             docker_compose_content = f.read()

    #         self.assertEqual(docker_compose_content["version"], "3.8")
    #         self.assertIn("redis-vector-db", docker_compose_content)
    #         self.assertIn("text-embeddings-inference-service", docker_compose_content)
    #     else:
    #         self.fail("Docker Compose file not generated.")


if __name__ == "__main__":
    unittest.main()
