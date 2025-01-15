# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

DATAPATH=$WORKDIR/TAG-Bench/tag_queries.csv
OUTFOLDER=$WORKDIR/TAG-Bench/query_by_db
python3 split_data.py --path $DATAPATH --output $OUTFOLDER
