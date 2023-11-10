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
from itertools import combinations

from utils import TESTING, find_bin, local_table_shards_dir, num_shards, stats_dir

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANGS

res_dir = stats_dir

if not os.path.exists(res_dir):
    os.makedirs(res_dir)


def compute_stats(bucket_num: int):
    """
    Computes stats for data from the given bucket
    """

    data_path = f"{local_table_shards_dir}/bucket{bucket_num:03}.json.gz"

    width = Counter()  # stores row widths per language
    width_hist = Counter()  # stores histogram of widths for all rows
    count = Counter()  # sent count per language
    lp_counts = (
        Counter()
    )  # stores counts of lang pairs and lang triplets in the bucket data

    len_per_lang_per_bin = {
        lang: Counter() for lang in CCMATRIX_LANGS
    }  # sum of number of characters in each translation_nums bin for each lang

    numrows_per_lang_per_bin = {lang: Counter() for lang in CCMATRIX_LANGS}

    row_count = 0
    sent_count = 0

    for ii, line in enumerate(gzip.open(data_path, "rt")):
        if ii % 1_000_000 == 0:
            print(f"progress: {ii:,}", flush=True)

        if TESTING and ii >= 1000:
            break

        # contains (sentence, margin score bin) for each language in the line
        line2 = json.loads(line)
        langs = list(line2.keys())  # all languages in that line
        langs.sort()

        num_translations = len(langs)  # number of translations of this line

        row_count += 1
        sent_count += num_translations

        width_hist[num_translations] += 1

        num_translations_bin = find_bin(num_translations)

        # for all langs
        for lang in langs:
            count[lang] += 1  # count of lang in data
            width[lang] += num_translations  # sum of row widths per lang

            sentence = line2[lang][0]
            sen_len = len(sentence)

            # for sentence lengths analysis
            len_per_lang_per_bin[lang][num_translations_bin] += sen_len
            numrows_per_lang_per_bin[lang][num_translations_bin] += 1

        # for all lang pairs
        for lang_pair in combinations(langs, 2):
            lp_counts[tuple(lang_pair)] += 1

        # for all lang triplets
        for lang_triplet in combinations(langs, 3):
            lp_counts[tuple(lang_triplet)] += 1

    return dict(
        lp_counts=lp_counts,
        count=count,
        width=width,
        width_hist=width_hist,
        row_count=row_count,
        sent_count=sent_count,
        len_per_lang_per_bin=len_per_lang_per_bin,
        numrows_per_lang_per_bin=numrows_per_lang_per_bin,
    )


if __name__ == "__main__":
    t0 = time.time()
    num_cpus = mp.cpu_count()

    with mp.Pool(num_cpus) as pool:
        res = pool.map(compute_stats, range(num_shards))

        res_sum = res[0]

        for resX in res[1:]:
            for key in res_sum:
                if (
                    key == "len_per_lang_per_bin" or key == "numrows_per_lang_per_bin"
                ):  # dict of counter
                    for bin_ in res_sum[key]:
                        res_sum[key][bin_] += resX[key][bin_]
                else:
                    res_sum[key] += resX[key]

        with open(f"{res_dir}/stats.pkl", "wb") as fout:
            pickle.dump(res_sum, fout)

    print(f"Computed stats in {time.time() - t0}s")
