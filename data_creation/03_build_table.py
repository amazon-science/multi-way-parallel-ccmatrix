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
Builds the multiway parallel data table
"""

import os
import pathlib
import pickle
import sys
from collections import Counter
from glob import glob
from time import time

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANGS
from config import bin_dir, hash2row_dir
from cykhash import Int64toInt64Map
from utils import entry_to_row_score, row_score_to_entry

numrows = 0
hash2row = {lang: Int64toInt64Map() for lang in CCMATRIX_LANGS}

t0 = time()
ii = 0

fnames = glob(f"{bin_dir}/*/*bin")
fnames.sort(
    key=lambda x: x.split("/")[-1], reverse=True
)  # sort from highest score/bin to lowest score/bin

# open all output files
out_files = dict()
pathlib.Path(f"{hash2row_dir}").mkdir(parents=True, exist_ok=True)
for lang in CCMATRIX_LANGS:
    out_files[lang] = open(f"{hash2row_dir}/{lang}.bin", "wb")


def add(lang, hh, entry):
    hash2row[lang][hh] = entry
    out_files[lang].write(hh.to_bytes(8, byteorder="little", signed=True))
    out_files[lang].write(entry.to_bytes(8, byteorder="little", signed=True))


def print_sizes():
    sizes = {lang: len(hash2row[lang]) for lang in CCMATRIX_LANGS}
    print("unique sentences per language:", Counter(sizes).most_common(), flush=True)
    total_size = sum([v for k, v in sizes.items()])
    print(f"total unique sentences: {total_size:,}", flush=True)
    print(f"num rows: {numrows:,}", flush=True)


for f_ii, fname in enumerate(fnames):
    num_lines_this_file = os.stat(fname).st_size / (2 * 8)
    print(
        f"processing {fname} (lines:{num_lines_this_file}) (file {f_ii + 1:,}/{len(fnames):,}), t={time() - t0:.1f}s",
        flush=True,
    )
    score_bin = int(
        fname.split("/")[-1].split(".")[0][len("bin") :]
    )  # bin{bin_idx:03}.bin'
    lang0, lang1 = fname.split("/")[-2].split("-")

    with open(fname, "rb", buffering=2**16) as fin:
        while True:
            ii += 1
            # convert hashes to int64-compatable int
            h0 = int.from_bytes(fin.read(8), byteorder="little", signed=True)
            h1 = int.from_bytes(fin.read(8), byteorder="little", signed=True)

            if not h1:  # end of file
                break

            # see if hashes allready added
            h0entry = hash2row[lang0].get(h0)  # get() returns None if not present
            h1entry = hash2row[lang1].get(h1)

            if h0entry is None and h1entry is None:
                # new entries, add pair as new row in table
                new_entry = row_score_to_entry(numrows, score_bin)
                add(lang0, h0, new_entry)
                add(lang1, h1, new_entry)
                numrows += 1
            elif h0entry is None:
                # h1 is already in table, add h0 to same row
                row1, _ = entry_to_row_score(h1entry)
                entry1 = row_score_to_entry(row1, score_bin)
                add(lang0, h0, entry1)
            elif h1entry is None:
                # h0 is already in table, add h1 to same row
                row0, _ = entry_to_row_score(h0entry)
                entry0 = row_score_to_entry(row0, score_bin)
                add(lang1, h1, entry0)
            # else they are both already in table (for higher scoring matches), nothing to do

            if ii % 5_000_000 == 0:
                print(
                    f"progress: {ii:,} sent pairs ({numrows:,} rows) in {time() - t0:.1f}s. sent_pair/sec::{ii / (time() - t0):.1f}",
                    flush=True,
                )

            if ii % 100_000_000 == 0:
                print_sizes()

# close all output files
for lang in CCMATRIX_LANGS:
    out_files[lang].close()

with open(f"{hash2row_dir}/numrows.pkl", "wb") as fout:
    pickle.dump(numrows, fout)

print(f"time: {time() - t0:.1f}s", flush=True)
print(f"num sent pairs: {ii:,}", flush=True)
print(f"Seconds per sent pair: {(time() - t0) / (ii + .01):.2e}", flush=True)
print_sizes()

print("done", flush=True)
