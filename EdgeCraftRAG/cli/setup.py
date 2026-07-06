#!/usr/bin/env python3
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Canonical setup script for EdgeCraft RAG CLI."""

from setuptools import setup

setup(
    name="ecrag-cli",
    version="0.1.0",
    description="Command-line interface for EdgeCraft RAG",
    author="Intel Corporation",
    license="Apache-2.0",
    packages=["cli"],
    package_dir={"": ".."},
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
    ],
    entry_points={
        "console_scripts": [
            "ecrag=cli.main:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
