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
Parses the raw CCMatrix bitext data, hashes each sentence and stores it in a subdirectory corresponding to its margin score bin.
"""

import gzip
import multiprocessing as mp
import os.path
import pathlib
import subprocess as sp
import sys
from time import time

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANG_PAIRS
from config import TESTING, bin_dir, cutoffs, exclude_num, find_bin, gz_dir
from utils import myhash


def hash_data(lang_pair):
    lang0, lang1 = lang_pair.split("-")  # in alphabetical order
    print("langs:", lang0, lang1, flush=True)

    outdir = f"{bin_dir}/{lang0}-{lang1}"
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)

    # open all output files
    fout = [
        open(os.path.join(outdir, f"bin{bin_idx:03}.bin.part"), "wb", buffering=2**16)
        for bin_idx in range(len(cutoffs) + 1)
    ]

    # process data
    gz_file = f"{gz_dir}/{lang0}-{lang1}.tsv.gz"
    t0 = time()
    done = 0
    with gzip.open(gz_file, "rt", encoding="utf-8") as csvfile:
        for ii, line in enumerate(csvfile):
            row = line.strip().split("\t")

            if ii % 1_000_000 == 0:
                print(
                    f"processed {ii:,} lines of {lang0}-{lang1} in {time() - t0:.1f}s",
                    flush=True,
                )

            if len(row) != 3:
                print("BAD ROW:", row, flush=True)
                continue

            score, src, tgt = row

            score = float(score)
            h0 = myhash(src)
            h1 = myhash(tgt)

            bin_idx = find_bin(score)
            fout[bin_idx].write(h0)
            fout[bin_idx].write(h1)

            done += 1

    for fh in fout:
        part_name = fh.name
        final_name = part_name[: -len(".part")]
        fh.close()
        sp.check_call(f"mv {part_name} {final_name}", shell=True)

    print(
        f"done: processed {done:,} lines of {lang0}-{lang1} in {time() - t0:.1f}s.",
        flush=True,
    )


if __name__ == "__main__":
    lang_pairs = CCMATRIX_LANG_PAIRS
    if TESTING:
        lang_pairs = lang_pairs[exclude_num:]

    num_cpus = mp.cpu_count()
    print(f"num language pairs: {len(lang_pairs)}, num cpus: {num_cpus}", flush=True)

    with mp.Pool(num_cpus) as pool:
        pool.map(hash_data, lang_pairs)
