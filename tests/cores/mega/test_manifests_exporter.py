# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import unittest

import yaml

from comps.cores.mega.manifests_exporter import build_chatqna_manifests


class TestChatQnAManifestsExporter(unittest.TestCase):
    def tearDown(self):
        file_path = "ChatQnA_E2E_manifests.yaml"

        try:
            os.remove(file_path)
            print(f"Deleted {file_path} OK")
        except FileNotFoundError:
            print(f"{file_path} Not Found")
        except OSError as e:
            print(f"Fail to delete: {e}")

    def test_manifests(self):
        build_chatqna_manifests()

        result = True
        with open("ChatQnA_E2E_manifests.yaml", "r") as f1, open("ChatQnA_E2E_manifests_base.yaml", "r") as f2:
            docs1 = yaml.safe_load_all(f1)
            docs2 = yaml.safe_load_all(f2)

            for doc1, doc2 in zip(docs1, docs2):
                if doc1 != doc2:
                    result = False

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
