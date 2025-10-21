from setuptools import setup, find_packages
import os
import sys
import platform

# Get the absolute path to the build directory
build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'build'))

# Determine the library extension based on the platform
if platform.system() == 'Windows':
    lib_ext = '.dll'
elif platform.system() == 'Darwin':
    lib_ext = '.dylib'
else:
    lib_ext = '.so'

# Find the library file
lib_name = f'libcogniware_engine_python{lib_ext}'
lib_path = os.path.join(build_dir, 'python', lib_name)

if not os.path.exists(lib_path):
    raise RuntimeError(f"Could not find {lib_name} in {os.path.dirname(lib_path)}")

setup(
    name='cogniware_engine',
    version='0.1.0',
    description='Python interface for MSmartCompute Engine',
    author='CogniDream',
    author_email='info@cognidream.com',
    packages=find_packages(),
    package_data={
        'cogniware_engine': [lib_name],
    },
    install_requires=[
        'numpy>=1.19.0',
        'torch>=1.9.0',
        'pybind11>=2.6.0',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
) 