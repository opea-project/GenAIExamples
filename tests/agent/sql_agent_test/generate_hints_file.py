# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import glob
import os

import pandas as pd


def generate_column_descriptions(db_name):
    descriptions = []
    working_dir = os.getenv("WORKDIR")
    assert working_dir is not None, "WORKDIR environment variable is not set."
    DESCRIPTION_FOLDER = os.path.join(
        working_dir, f"TAG-Bench/dev_folder/dev_databases/{db_name}/database_description/"
    )
    table_files = glob.glob(os.path.join(DESCRIPTION_FOLDER, "*.csv"))
    table_name_col = []
    col_name_col = []
    for table_file in table_files:
        table_name = os.path.basename(table_file).split(".")[0]
        print("Table name: ", table_name)
        df = pd.read_csv(table_file)
        for _, row in df.iterrows():
            col_name = row["original_column_name"]
            if not pd.isnull(row["value_description"]):
                description = str(row["value_description"])
                if description.lower() in col_name.lower():
                    print("Description {} is same as column name {}".format(description, col_name))
                    pass
                else:
                    description = description.replace("\n", " ")
                    description = " ".join(description.split())
                    descriptions.append(description)
                    table_name_col.append(table_name)
                    col_name_col.append(col_name)
    hints_df = pd.DataFrame({"table_name": table_name_col, "column_name": col_name_col, "description": descriptions})
    tag_bench_dir = os.path.join(working_dir, "TAG-Bench")
    output_file = os.path.join(tag_bench_dir, f"{db_name}_hints.csv")
    hints_df.to_csv(output_file, index=False)
    print(f"Generated hints file: {output_file}")


if __name__ == "__main__":
    generate_column_descriptions("california_schools")
