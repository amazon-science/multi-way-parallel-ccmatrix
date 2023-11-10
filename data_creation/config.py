#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


TESTING = False # if TESTING is true, exclude the first exclude_num lang pairs while processing
exclude_num = 500

num_score_bins = 50  # number of score bins to create
bin_edge_prec = 100_000  # precision of bin edges
num_buckets = 100  # number of table shards

gz_dir = "raw_data"  # 849G, stores raw ccMatrix data
bin_dir = "binned_data"  # 162G, stores binary hash of each sentence pair in ccMatrix, binned by margin score
hash2row_dir = (
    "tables_hashed"  # 118G, stores sentence hash -> (row, bined margin score)
)
hash2sent_dir = "hash2sent"  # 395G, stores sentence hash -> sentence and sentence hash -> (row, binned margin score), sharded into output folders
shard_dir = "shards"  # 296G, stores final table, one json line per entry, gzipped
cutoffs_file = "cutoffs.txt"  # Stores cutoffs for the score bin edges. Created in 01_create_bin_edges.py

cutoffs = []

import os

if os.path.exists(cutoffs_file):  # if the cutoffs file has been created
    with open(cutoffs_file, "r") as fr:
        cutoffs = fr.read().split("\n")
    cutoffs.pop()  # empty line
    cutoffs = [float(x) for x in cutoffs]


import bisect


def find_bin(score):
    """
    Find the bin corresponding to a given score
    """
    return bisect.bisect_left(cutoffs, score)


bin_numbers = list(range(find_bin(100), find_bin(0) - 1, -1))
