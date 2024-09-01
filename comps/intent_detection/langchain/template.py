# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class IntentTemplate:
    def generate_intent_template(query):
        return f"""Please identify the intent of the user query. You may only respond with "chitchat" or "QA" without explanations or engaging in conversation.
### User Query: {query}, ### Response: """
