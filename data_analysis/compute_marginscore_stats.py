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


import gzip
import json
import multiprocessing as mp
import os
import pickle
import sys
import time
from collections import Counter

from utils import (
    TESTING,
    bin_to_score_mapping,
    find_bin,
    local_table_shards_dir,
    marginscore_with_len_analysis_list,
    num_shards,
    num_translations_cutoffs,
    stats_dir,
)

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANGS

res_dir = stats_dir


def compute_stats(bucket_num):
    data_path = f"{local_table_shards_dir}/bucket{bucket_num:03}.json.gz"

    ms_sum = {
        lang: Counter() for lang in CCMATRIX_LANGS
    }  # sum of margin score for each lang in each num_translations bin
    ms_len_list_per_bin = {
        lang: {bin_: [] for bin_ in range(len(num_translations_cutoffs) + 1)}
        for lang in marginscore_with_len_analysis_list
    }  # stores list of sentence margin scores for each bin of # translations (only for langs in the list)

    for ii, line in enumerate(gzip.open(data_path, "rt")):
        if ii % 1_000_000 == 0:
            print(f"progress: {ii:,}", flush=True)

        if TESTING and ii > 1000:
            break

        line2 = json.loads(line)

        num_translations = len(line2)
        num_translations_bin = find_bin(num_translations)

        for lang in line2:
            score_bin = line2[lang][1]  # keep upper score of the bin
            score = bin_to_score_mapping[score_bin]

            ms_sum[lang][
                num_translations_bin
            ] += score  # add the score to the sum of scores for that language in that translations bin

            if lang in marginscore_with_len_analysis_list:
                sentence = line2[lang][0]
                sen_len = len(sentence)
                ms_len_list_per_bin[lang][num_translations_bin].append((score, sen_len))

    return dict(ms_sum=ms_sum, ms_len_list_per_bin=ms_len_list_per_bin)


if __name__ == "__main__":
    t0 = time.time()

    num_cpus = mp.cpu_count()

    with mp.Pool(num_cpus) as pool:
        all_res = pool.map(compute_stats, range(num_shards))

        print(f"Computed stats from all buckets. Starting combine")

        ms_sum = {lang: Counter() for lang in CCMATRIX_LANGS}
        ms_len_list_per_bin = {
            lang: {bin_: [] for bin_ in range(len(num_translations_cutoffs) + 1)}
            for lang in marginscore_with_len_analysis_list
        }

        for res in all_res:
            for lang in res["ms_sum"].keys():
                ms_sum[lang] += res["ms_sum"][lang]
            for lang in res["ms_len_list_per_bin"].keys():
                for bin_ in res["ms_len_list_per_bin"][lang].keys():
                    ms_len_list_per_bin[lang][bin_] += res["ms_len_list_per_bin"][lang][
                        bin_
                    ]

        with open(f"{res_dir}/marginscore_stats.pkl", "wb") as fout:
            pickle.dump(ms_sum, fout)

        for lang in marginscore_with_len_analysis_list:
            with open(f"{res_dir}/marginscore_with_len_{lang}.pkl", "wb") as fout:
                pickle.dump(ms_len_list_per_bin, fout)

    print(f"Computed stats in {time.time()-t0}s")
