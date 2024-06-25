# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import errno
import functools
import hashlib
import os
import signal
import timeit
from pathlib import Path


class Timer:
    level = 0
    viewer = None

    def __init__(self, name):
        self.name = name
        if Timer.viewer:
            Timer.viewer.display(f"{name} started ...")
        else:
            print(f"{name} started ...")

    def __enter__(self):
        self.start = timeit.default_timer()
        Timer.level += 1

    def __exit__(self, *a, **kw):
        Timer.level -= 1
        if Timer.viewer:
            Timer.viewer.display(f'{"  " * Timer.level}{self.name} took {timeit.default_timer() - self.start} sec')
        else:
            print(f'{"  " * Timer.level}{self.name} took {timeit.default_timer() - self.start} sec')


class TimeoutError(Exception):
    pass


def save_logs(log_name, data):
    import pandas as pd

    df = pd.DataFrame.from_records(data)
    try:
        dir_path = os.path.dirname(log_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        df.to_csv(log_name)
    except:
        pass
    return df


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator


def generate_log_name(file_list):
    file_set = f"{sorted(file_list)}"
    # print(f"file_set: {file_set}")
    md5_str = hashlib.md5(file_set.encode()).hexdigest()
    return f"status/status_{md5_str}.log"


def get_failable_with_time(callable):
    def failable_callable(*args, **kwargs):
        start_time = timeit.default_timer()
        try:
            content = callable(*args, **kwargs)
            error = None
        except Exception as e:
            content = None
            error = str(e)
        end_time = timeit.default_timer()
        return content, error, f"{'%.3f' % (end_time - start_time)}"

    return failable_callable


def prepare_env(enable_ray=False, pip_requirements=None, comps_path=None):
    if enable_ray:
        import ray

        if ray.is_initialized():
            ray.shutdown()
        if pip_requirements is not None:
            ray.init(runtime_env={"pip": pip_requirements, "env_vars": {"PYTHONPATH": comps_path}})
        else:
            ray.init(runtime_env={"env_vars": {"PYTHONPATH": comps_path}})


def get_max_cpus(total_num_tasks):
    num_cpus_available = os.cpu_count()
    num_cpus_per_task = num_cpus_available // total_num_tasks
    if num_cpus_per_task == 0:
        return 8
    return num_cpus_per_task


async def save_file_to_local_disk(save_path: str, file):
    save_path = Path(save_path)
    with save_path.open("wb") as fout:
        try:
            content = await file.read()
            fout.write(content)
        except Exception as e:
            print(f"Write file failed. Exception: {e}")
            raise SystemError(f"Write file {save_path} failed. Exception: {e}")
