#!/usr/bin/env python3
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Install the CA bundle if required.

Attempt to connect to a test URL. If it fails due to an SSL error,
install the CA bundle and try again.
"""

import os
import shutil
import sys
import tempfile
import zipfile
from typing import Iterable, Optional

import certifi
import requests
import timeout as t

CERT_BASE_URL = "http://certificates.intel.com/repository/certificates"
CERTS = (f"{CERT_BASE_URL}/IntelSHA2RootChain-Base64.zip",)
SERVER_TIMEOUT = t.http_timeout()
TEST_URLS = ("https://bdba001.icloud.intel.com/api/status", "https://sast.intel.com/cxrestapi/projects")


@t.handle_timeouts
def ssl_error(test_urls: Iterable[str] = TEST_URLS) -> bool:
    """Return True if we get an SSL error for any of the test_urls."""
    ssl_errors = []
    for test_url in test_urls:
        try:
            with requests.get(test_url, timeout=SERVER_TIMEOUT) as _:  # nosec
                return False
        except requests.exceptions.SSLError:
            ssl_errors.append(test_url)
        except requests.exceptions.RequestException as exc:
            print(f"Warning, unable to connect to {test_url}: {exc}", file=sys.stderr)
    return bool(ssl_errors)


@t.handle_timeouts
def download_certificate_zip(source_url: str, dest_dir: Optional[str] = None):
    """Download the zip file containing the CA certificates."""
    # pylint: disable=consider-using-with
    temp_zip = tempfile.NamedTemporaryFile(delete=False, dir=dest_dir)
    with requests.get(source_url, stream=True, timeout=SERVER_TIMEOUT) as req:
        with open(temp_zip.name, "wb") as file_handle:
            shutil.copyfileobj(req.raw, file_handle)
    return temp_zip


def append_bundle(source, dest=certifi.where(), extract_dir=None) -> None:
    """Append certificates to the dest CA certificate bundle."""
    with zipfile.ZipFile(source) as zip_file:
        for cert_file in zip_file.infolist():
            path = zip_file.extract(cert_file, path=extract_dir)
            pth_lower = path.lower()
            if not (pth_lower.endswith(".cer") or pth_lower.endswith(".crt")):
                continue
            with open(dest, "a+", encoding="utf-8") as file_handle:
                with open(path, encoding="utf-8") as cert_path:
                    file_handle.write(cert_path.read())
            os.remove(path)


def install_ca_bundle(source_url: str, temp_dir: Optional[str] = None) -> None:
    """Download the certificates and append them to the CA bundle file."""
    cert_zip = download_certificate_zip(source_url, temp_dir)
    try:
        append_bundle(cert_zip, extract_dir=temp_dir)
    finally:
        os.remove(cert_zip.name)
        cert_zip.close()


def install_ca_bundles(certs: Iterable[str] = CERTS) -> None:
    """Install the trusted CA bundle(s)."""
    for cert_zip_url in certs:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_ca_bundle(cert_zip_url, temp_dir)


def main():
    """Main program."""
    if ssl_error():
        install_ca_bundles()
    if ssl_error():
        print("ERROR, failed to connect using SSL.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
