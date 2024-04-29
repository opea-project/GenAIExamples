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
"""Client for interacting with the BDBA server using its API."""

import argparse
import json
import logging
import os
import pathlib
import re
import sys
import time

import requests

err_logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

API_URL_MAP = {
    "upload": "{baseurl}/api/upload/{filename}",
    "result": "{baseurl}/api/product/{product}",
    "export": "{baseurl}/api/product/{product}/csv-vulns",
    "components": "{baseurl}/api/product/{product}/csv-libs",
}
COMPONENTS_TASK_ID = os.environ.get("COMPONENTS_TASK_ID", "CT36")
CVE_TASK_ID = os.environ.get("CVE_TASK_ID", "CT7")
MAX_GROUP_ID = 9999
MAX_PROJECT_ID = 9999999
WORKSPACE = pathlib.Path(os.environ.get("GITHUB_WORKSPACE", pathlib.Path.cwd()))


def _validate_project_id(project_id):
    """Ensure the project ID is formatted correctly."""
    try:
        project_id_int = int(project_id)
    except (TypeError, ValueError) as exc:
        err_logger.critical("SDL project ID must be an integer.")
        err_logger.critical(exc)
        sys.exit(1)
    if (project_id_int < 0) or (project_id_int > MAX_PROJECT_ID):
        err_logger.critical("Project ID must be between 0 and " "%s.", MAX_PROJECT_ID)
        sys.exit(2)


def _validate_task_id(task_id):
    """Ensure the SD Elements task ID is formatted correctly."""
    regex = "^C?T[1-9][0-9]{0,3}$"
    if not re.search(regex, task_id):
        err_logger.critical('The task ID "%s" must match the ' "regular expression: %s", task_id, regex)
        sys.exit(3)


def _validate_baseurl(url: str) -> None:
    """Ensure the baseurl is a valid Intel HTTPS URL."""
    url = url.strip()
    regex = re.compile(
        "^https:[/][/]([-a-zA-Z0-9@:%_+~#=]([.](?![.]))*){0,251}[.]intel[.]com"
        "([/](?![/])([-a-zA-Z0-9@:%_+~#?&=]([./()](?![./?&=%@:()#]))*)*)?$"
    )
    if not regex.search(url):
        print("Error, the supplied URL is not a valid Intel HTTPS URL: " f'"{url}".', file=sys.stderr)
        sys.exit(4)


def _validate_file(file_path: pathlib.Path) -> None:
    """Ensure the file_path provided exists and is within the WORKSPACE."""
    sanitized_path = pathlib.Path(file_path).resolve()
    if os.path.commonpath([WORKSPACE, sanitized_path]) != str(WORKSPACE):
        print(f"Error, {file_path} is not within {WORKSPACE}", file=sys.stderr)
        sys.exit(5)
    if not sanitized_path.exists():
        print(f"Error, {file_path} does not exist.", file=sys.stderr)
        sys.exit(6)


def _validate_group(group_id: int) -> None:
    """Ensure the group_id is a valid integer."""
    if not isinstance(group_id, int):
        print(f"Error, group ID ({group_id}) is not an integer.", file=sys.stderr)
        sys.exit(7)
    if (group_id < 0) or (group_id > MAX_GROUP_ID):
        print(f"Error, group ID ({group_id}) must be between 0 and " f"{MAX_GROUP_ID}", file=sys.stderr)
        sys.exit(8)


def _validate_outdir(outdir: pathlib.Path) -> None:
    """Ensure the outdir exists and is a directory."""
    if not pathlib.Path(outdir).is_dir():
        print(f"Error, the output directory ({outdir}) is not a directory.", file=sys.stderr)
        sys.exit(9)


def default_project_id():
    """Return the SD Elements project ID or 0."""
    project_id = os.environ.get("SDL_PROJECT_ID", 0)
    _validate_project_id(project_id)
    return int(project_id)


class APITokenNotFoundError(Exception):
    """API Token for BDBA was not found."""


class NoMoreRetriesError(Exception):
    """Out of Retries."""


# pylint: disable=too-many-instance-attributes
class BDBA:
    """Enable BDBA API Client to analyze files for vulnerabilities."""

    STATUS_BUSY = "B"

    def __init__(self, args, api_token):
        if not os.path.isfile(args.file):
            raise FileNotFoundError(f"File, {args.file}, was not found")
        self.api_token = api_token
        self.baseurl = args.baseurl
        self.components_task_id = args.components_task_id
        self.cve_task_id = args.cve_task_id
        self.sdl_project_id = args.sdl_project_id
        self.file = args.file
        # Get rid of any unsupported characters in the file name
        self.filename = re.sub(r"[^\w._-]", "_", os.path.basename(self.file))
        self.group = args.group
        self.outdir = args.outdir

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    def _get_uri(self, end_point, **params):
        """Resolve URI with given API end points."""
        route = API_URL_MAP[end_point]
        params.setdefault("baseurl", self.baseurl)
        return route.format(**params)

    def _retry(self, func, *args, **kwargs):
        """Retry requests that returned an error up to MAX_ATTEMPTS."""
        retry_exceptions = (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
        )
        max_attempts = 5
        for _ in range(max_attempts):
            try:
                response = func(*args, **kwargs)
            except retry_exceptions as error:
                logger.info("Connection failed: %s, retrying...", error)
                time.sleep(30)
                continue
            else:
                return response
        raise NoMoreRetriesError("Out of Retries.")

    def export_components(self, product):
        """Export components to a CSV file."""
        uri = self._get_uri("components", product=product)
        response = self._retry(self.session.get, uri)
        response.raise_for_status()
        components_csv = f"{self.outdir}/{self.components_task_id}_" "BDBA-components.csv"
        if self.sdl_project_id > 0:
            components_csv = f"{self.outdir}/{self.components_task_id}_" f"{self.sdl_project_id}-BDBA-components.csv"
        with open(components_csv, "wb") as csv:
            csv.write(response.content)
        logger.info("Components list downloaded to %s", components_csv)

    def export_result(self, product):
        """Export CVE results to a CSV file."""
        uri = self._get_uri("export", product=product)
        response = self._retry(self.session.get, uri)
        response.raise_for_status()
        result_csv = f"{self.outdir}/{self.cve_task_id}_bdba_results.csv"
        with open(result_csv, "wb") as csv:
            csv.write(response.content)
        logger.info("CVE results downloaded to %s", result_csv)

    def get_result_status(self, product):
        """Get the result status of a scan."""
        uri = self._get_uri("result", product=product)
        response = self._retry(self.session.get, uri)
        response.raise_for_status()
        data = json.loads(response.text)
        result = data.get("results", {}).get("status", "")
        return result

    def upload_file(self):
        """Upload a binary file for analyzing and write the CSV results."""
        uri = self._get_uri("upload", filename=self.filename)
        self.session.headers.update({"Group": f"{self.group}"})
        logger.info("uploading file...")
        with open(self.file, "rb") as data:
            response = self._retry(self.session.put, uri, data=data)
        response.raise_for_status()
        data = json.loads(response.text)
        product_id = data.get("results", {}).get("product_id")
        logger.info("Uploaded %s with ID: %s", self.file, product_id)

        while True:
            logger.info("Polling...")
            if self.get_result_status(product_id) == BDBA.STATUS_BUSY:
                time.sleep(5)
                continue
            break
        self.export_result(product_id)
        self.export_components(product_id)


def configure_error_logger():
    """Configure logging of errors."""
    err_logger.setLevel(logging.WARN)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    handler.setLevel(logging.INFO)
    err_logger.addHandler(handler)


def configure_logger():
    """Configure logger to format log lines and set up console logging."""
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


def get_token():
    """Get the API token for login."""
    api_token = os.environ.get("BDBA_TOKEN")
    if api_token is not None:
        return api_token
    token = os.path.abspath(os.path.expanduser("~/.bdba/api_token"))
    if not os.path.exists(token):
        raise APITokenNotFoundError("No BDBA API token found.")
    with open(token, "r", encoding="utf-8") as token_file:
        api_token = token_file.readline().rstrip()
    return api_token


def cli_arguments() -> argparse.Namespace:
    """Return an argparse object containing CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=pathlib.Path,
        help="file that will be analyzed",
    )
    parser.add_argument(
        "-b",
        "--baseurl",
        required=True,
        type=str,
        help="base URL of the BDBA server",
    )
    parser.add_argument(
        "-g",
        "--group",
        required=True,
        type=int,
        help="BDBA group for your project",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        required=True,
        type=pathlib.Path,
        help="directory where output will be written",
    )
    parser.add_argument(
        "-c",
        "--components-task-id",
        default=COMPONENTS_TASK_ID,
        type=str,
        help=("SDL task ID for listing components " f"(default: {COMPONENTS_TASK_ID})"),
    )
    parser.add_argument(
        "-i",
        "--cve-task-id",
        default=CVE_TASK_ID,
        type=str,
        help=f"SDL task ID for CVEs (default: {CVE_TASK_ID})",
    )
    parser.add_argument(
        "-p",
        "--sdl-project-id",
        default=default_project_id(),
        type=int,
        help=("SD Elements project ID used for evidence " f"(default: {default_project_id()})"),
    )
    cli_args: argparse.Namespace = parser.parse_args()

    # Validate inputs
    _validate_baseurl(cli_args.baseurl)
    _validate_task_id(cli_args.components_task_id)
    _validate_task_id(cli_args.cve_task_id)
    _validate_project_id(cli_args.sdl_project_id)
    _validate_file(cli_args.file)
    _validate_group(cli_args.group)
    _validate_outdir(cli_args.outdir)
    return cli_args


def main():
    """This module wraps around Black Duck Binary Analysis' API to analyze a
    given file for their known vulnerabilities."""
    args = cli_arguments()
    configure_error_logger()
    configure_logger()

    api_token = get_token()
    bdba = BDBA(args, api_token)
    bdba.upload_file()


if __name__ == "__main__":
    main()
