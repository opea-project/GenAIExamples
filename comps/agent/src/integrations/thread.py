# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections import deque
from datetime import datetime
from uuid import uuid4

from .global_var import threads_global_kv


class ThreadMemory:
    def __init__(self):
        self.query_list = deque()

    def add_query(self, query):
        msg_id = f"msg_{uuid4()}"
        created_at = int(datetime.now().timestamp())

        self.query_list.append((query, msg_id, created_at))

        return msg_id, created_at

    def get_query(self):
        query, _, _ = self.query_list.pop()
        return query


async def thread_completion_callback(content, thread_id):
    with threads_global_kv as g_threads:
        thread_inst, created_at, _ = g_threads[thread_id]
        g_threads[thread_id] = (thread_inst, created_at, "running")
    print("[thread_completion_callback] Changed status to running")
    async for chunk in content:
        if "data: [DONE]\n\n" == chunk:
            with threads_global_kv as g_threads:
                thread_inst, created_at, _ = g_threads[thread_id]
                g_threads[thread_id] = (thread_inst, created_at, "ready")
        yield chunk


def instantiate_thread_memory(args=None):
    thread_id = f"thread_{uuid4()}"
    return ThreadMemory(), thread_id
