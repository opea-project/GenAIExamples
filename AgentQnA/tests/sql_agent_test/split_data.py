# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os

import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    # if output folder does not exist, create it
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # Load the data
    data = pd.read_csv(args.path)

    # Split the data by domain
    domains = data["DB used"].unique()
    for domain in domains:
        domain_data = data[data["DB used"] == domain]
        out = os.path.join(args.output, f"query_{domain}.csv")
        domain_data.to_csv(out, index=False)
