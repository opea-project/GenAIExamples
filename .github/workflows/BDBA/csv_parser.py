#!/usr/bin/env python3
"""Parse CSV report. Exit with error code if vulnerabilities are found.

If environment variable IGNORE_TRIAGED is set to "true", exit successfully
(i.e. exit 0) if all vulnerability rows are marked as triaged.
"""

import argparse
import os
import pathlib
import sys

import pandas  # type: ignore # pylint: disable=import-error

IGNORE_TRIAGED = "IGNORE_TRIAGED"


def _validate_csv_file(csv_file: pathlib.Path) -> None:
    """Exit with a user-friendly message if the csv_file is not found."""
    if not csv_file.is_file():
        print(f'Error, CSV file "{csv_file}" not found. Exiting',
              file=sys.stderr)
        sys.exit(3)


def mkdir(directory: pathlib.Path) -> None:
    """Create directory tree. Abort if non-directory file already exists."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        print(f'Error, the directory "{directory}" could not be created. '
              'An existing non-directory file already exists with the same '
              'name.', file=sys.stderr)
        sys.exit(6)


def get_vulnerabilities(csv_file: pathlib.Path) -> pandas.DataFrame:
    """Return vulnerabilities as a pandas DataFrame."""
    print(f'\n\nParsing results from file: {csv_file}')
    data: pandas.DataFrame = pandas.read_csv(csv_file)

    query = "(CVSS3 != 0 or (CVSS3 == 0 or CVSS3 != CVSS3) and CVSS >= 0)"
    if os.getenv(IGNORE_TRIAGED) == "true":
        print("\n\nIgnoring triaged vulnerabilities")
        query += " and `Triage vectors`.isnull()"
    else:
        print(
            f"\n\n{IGNORE_TRIAGED} not set, "
            "all vulnerabilities with CVSS scores will be considered."
        )

    return data.query(query)


def exit_(vulns: pandas.DataFrame) -> None:
    """Exit with a non-zero code if any vulnerabilities are found."""
    if vulns.empty:
        sys.exit(0)
    sys.exit(1)


def cli_input() -> argparse.Namespace:
    """Return an argparse object containing values from user CLI input."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        'CSV_FILE',
        type=pathlib.Path,
        help='path to the file to analyze',
    )
    cli_args = parser.parse_args()
    _validate_csv_file(cli_args.CSV_FILE)
    return cli_args


def main() -> None:
    """Inspect the CSV file for vulnerabilities and write a report."""
    args: argparse.Namespace = cli_input()
    vulns: pandas.DataFrame = get_vulnerabilities(args.CSV_FILE)
    exit_(vulns)


if __name__ == '__main__':
    main()