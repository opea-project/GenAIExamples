# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import threading


class ThreadSafeDict(dict):
    def __init__(self, *p_arg, **n_arg):
        dict.__init__(self, *p_arg, **n_arg)
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self._lock.release()


assistants_global_kv = ThreadSafeDict()
threads_global_kv = ThreadSafeDict()
