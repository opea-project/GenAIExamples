# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import platform
from datetime import datetime

import cpuinfo
import distro
import openvino.runtime as ov
import psutil
from fastapi import FastAPI, HTTPException, status


def get_available_devices():
    core = ov.Core()
    avail_devices = core.available_devices + ["AUTO"]
    if "NPU" in avail_devices:
        avail_devices.remove("NPU")
    return avail_devices


def get_system_status():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    memory_total_gb = memory_info.total / (1024**3)
    memory_used_gb = memory_info.used / (1024**3)
    # uptime_seconds = time.time() - psutil.boot_time()
    # uptime_hours, uptime_minutes = divmod(uptime_seconds // 60, 60)
    disk_usage = psutil.disk_usage("/").percent
    # net_io = psutil.net_io_counters()
    os_info = platform.uname()
    kernel_version = os_info.release
    processor = cpuinfo.get_cpu_info()["brand_raw"]
    dist_name = distro.name(pretty=True)

    now = datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M")
    status = {
        "cpuUsage": cpu_usage,
        "memoryUsage": memory_usage,
        "memoryUsed": memory_used_gb,
        "memoryTotal": memory_total_gb,
        "diskUsage": disk_usage,
        "kernel": kernel_version,
        "processor": processor,
        "os": dist_name,
        "currentTime": current_time_str,
    }
    return status


system_app = FastAPI()


# GET Syetem info
@system_app.get(path="/v1/system/info")
async def get_system_info():
    try:
        return get_system_status()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# GET available devices info
@system_app.get(path="/v1/system/device")
async def get_device_info():
    try:
        return get_available_devices()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
