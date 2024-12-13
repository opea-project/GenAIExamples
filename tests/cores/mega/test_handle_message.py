# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from typing import Union

from comps.cores.mega.utils import handle_message


class TestHandleMessage(unittest.IsolatedAsyncioTestCase):

    def test_handle_message(self):
        messages = [
            {"role": "user", "content": "opea project! "},
        ]
        prompt = handle_message(messages)
        self.assertEqual(prompt, "user: opea project! \n")

    def test_handle_message_with_system_prompt(self):
        messages = [
            {"role": "system", "content": "System Prompt"},
            {"role": "user", "content": "opea project! "},
        ]
        prompt = handle_message(messages)
        self.assertEqual(prompt, "System Prompt\nuser: opea project! \n")

    def test_handle_message_with_image(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello, "},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                    },
                ],
            },
        ]
        prompt, image = handle_message(messages)
        self.assertEqual(prompt, "user: hello, \n")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ""},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                    },
                ],
            },
        ]
        prompt, image = handle_message(messages)
        self.assertEqual(prompt, "user:")

    def test_handle_message_with_image_str(self):
        self.img_b64_str = (
            "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello, "},
                    {
                        "type": "image_url",
                        "image_url": {"url": self.img_b64_str},
                    },
                ],
            },
        ]
        prompt, image = handle_message(messages)
        self.assertEqual(image[0], self.img_b64_str)

    def test_handle_message_with_image_local(self):
        img_b64_str = (
            "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"
        )
        import base64
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(base64.decodebytes(bytes(img_b64_str, "utf-8"))))
        img.save("./test.png")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello, "},
                    {
                        "type": "image_url",
                        "image_url": {"url": "./test.png"},
                    },
                ],
            },
        ]
        prompt, image = handle_message(messages)
        self.assertEqual(prompt, "user: hello, \n")

    def test_handle_message_with_content_list(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello, "},
                ],
            },
            {"role": "assistant", "content": "opea project! "},
            {"role": "user", "content": ""},
        ]
        prompt = handle_message(messages)
        self.assertEqual(prompt, "user:assistant: opea project! \n")

    def test_handle_string_message(self):
        messages = "hello, "
        prompt = handle_message(messages)
        self.assertEqual(prompt, "hello, ")

    def test_handle_message_with_invalid_role(self):
        messages = [
            {"role": "user_test", "content": "opea project! "},
        ]
        self.assertRaises(ValueError, handle_message, messages)


if __name__ == "__main__":
    unittest.main()
