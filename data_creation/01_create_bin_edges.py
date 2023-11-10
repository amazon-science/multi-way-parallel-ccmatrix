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


"""
Create roughly equal sized bins from scores ccmatrix, saves cutoffs in cutoffs.txt
"""

import gzip
import math
import multiprocessing as mp
import sys
from collections import Counter
from time import time

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANG_PAIRS
from config import (
    TESTING,
    bin_edge_prec,
    cutoffs_file,
    exclude_num,
    gz_dir,
    num_score_bins,
)


def get_scores_counter(langpair):
    scores_count = Counter()
    total_rows = 0

    gz_file = f"{langpair}.tsv.gz"
    file_path = f"{gz_dir}/{gz_file}"
    t0 = time()
    with gzip.open(file_path, "rt", encoding="utf-8") as csvfile:
        for ii, line in enumerate(csvfile):
            row = line.strip().split("\t")

            if ii % 1_000_000 == 0:
                print(
                    f"processed {ii:,} lines of {langpair} in {time() - t0:.1f}s",
                    flush=True,
                )

            if len(row) != 3:
                print("BAD ROW:", row, flush=True)
                continue
            score = row[0]
            score_bucket = int(float(score) * bin_edge_prec)
            scores_count[score_bucket] += 1
            total_rows += 1

    print(f"all lines processed in {time() - t0:.1f}s", flush=True)
    return scores_count, total_rows


if __name__ == "__main__":
    t0 = time()
    lang_pairs = CCMATRIX_LANG_PAIRS

    if TESTING:
        lang_pairs = lang_pairs[exclude_num:]

    num_cpus = mp.cpu_count()

    with mp.Pool(num_cpus) as pool:
        counter_total = pool.map(get_scores_counter, lang_pairs)

        scores_count = Counter()
        total_rows = 0
        for ii, val in enumerate(counter_total):
            scores_count.update(val[0])
            total_rows += val[1]

    rows_per_bin = math.ceil(
        total_rows / num_score_bins
    )  # this is approximate since the distribution for each score is not uniform

    print(f"Total rows: {total_rows}")
    print(f"Rows per bin: {rows_per_bin}")

    all_scores = list(scores_count.keys())
    all_scores.sort()

    bin_edges = {}
    rows_in_bin = 0
    for ii, score in enumerate(
        all_scores
    ):  # we may end up with more than num_score_bins but this will ensure no bin has disproportionately high examples
        if ii == len(all_scores) - 1:  # last score
            bin_edges[score] = rows_in_bin + scores_count[score]
        elif rows_in_bin + scores_count[score] > rows_per_bin:
            bin_edges[score] = rows_in_bin
            rows_in_bin = scores_count[score]
        else:
            rows_in_bin += scores_count[score]

    print(f"Number of bins: {len(bin_edges)}", flush=True)

    edges = list(bin_edges.keys())
    cutoffs = [x / bin_edge_prec for x in edges]
    cutoffs.sort()
    cutoffs.pop()

    with open(cutoffs_file, "w") as fw:
        for c in cutoffs:
            fw.write(f"{c}\n")

    print(f"Created {len(cutoffs)} cutoffs in {time()-t0}s", flush=True)
