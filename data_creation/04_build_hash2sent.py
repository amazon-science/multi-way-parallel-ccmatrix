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
Parses the file for all languages in the `tables_hashed` directory, and maps each hashed entry to its sentence, row and margin score bin.
"""

import gzip
import multiprocessing as mp
import os
import pathlib
import sys
from glob import glob
from time import time

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANGS
from config import gz_dir, hash2row_dir, hash2sent_dir, num_buckets
from cykhash import Int64Set, Int64toInt64Map
from utils import entry_to_row_score, myhash, myhash2int


def go(lang):
    t0 = time()
    hash2entry = Int64toInt64Map()
    fname = f"{hash2row_dir}/{lang}.bin"
    num_to_read = os.stat(fname).st_size // 16
    bfile = open(fname, "rb")
    read = 0
    while True:
        hash_bytes = bfile.read(8)
        row_score_bytes = bfile.read(8)
        if not row_score_bytes:  # EOF
            break
        read += 1
        hash_int = myhash2int(hash_bytes)
        row, score = entry_to_row_score(myhash2int(row_score_bytes))
        hash2entry[hash_int] = myhash2int(row_score_bytes)
        if read % 10_000_000 == 0:
            print(
                f"read {read:,} of {num_to_read:,} lang {lang} hashes from disk, t={time() - t0:.1f}s",
                flush=True,
            )
    t1 = time()
    print(
        f"lang {lang} read {len(hash2entry):,} hash->row entries in {t1 - t0:.1f}s",
        flush=True,
    )

    seen = Int64Set()
    t0 = time()

    lines_read = 0
    gz_files = glob(f"{gz_dir}/*.tsv.gz")
    my_files = []
    for fname in gz_files:
        lang0, lang1 = fname.split("/")[1].split(".")[0].split("-")
        if lang in (lang0, lang1):
            my_files.append(fname)

    out_files = dict()
    for bucket in range(num_buckets):
        pathlib.Path(f"{hash2sent_dir}/bucket{bucket:03}").mkdir(
            parents=True, exist_ok=True
        )
        out_files[bucket] = dict()
        out_files[bucket]["text"] = gzip.open(
            f"{hash2sent_dir}/bucket{bucket:03}/hash2sent_{lang}.txt.gz", "wt"
        )
        out_files[bucket]["bin"] = open(
            f"{hash2sent_dir}/bucket{bucket:03}/hash2sent_{lang}.bin", "wb"
        )

    for fname_ii, fname in enumerate(my_files):
        lang0, lang1 = fname.split("/")[1].split(".")[0].split("-")
        with gzip.open(fname, "rt", encoding="utf-8") as csvfile:
            for _, line in enumerate(csvfile):
                lines_read += 1
                row = line.strip().split("\t")
                score, src, tgt = row
                mysent = src if lang == lang0 else tgt
                hh = myhash(mysent)
                hh_int = myhash2int(hh)
                if hh_int not in seen:
                    seen.add(hh_int)
                    mysent = mysent.replace("\n", " ").replace("\t", " ").strip() + "\n"
                    entry = hash2entry[hh_int]
                    row, _ = entry_to_row_score(entry)
                    bucket = row % num_buckets
                    out_files[bucket]["text"].write(mysent)
                    out_files[bucket]["bin"].write(hh)
                    out_files[bucket]["bin"].write(
                        entry.to_bytes(8, byteorder="little", signed=True)
                    )

                if lines_read % 1_000_000 == 0:
                    print(
                        f"lang={lang}, file {fname} ({fname_ii}/{len(my_files)}), lines read: {lines_read:,}, unique:{len(seen):,}, t={time() - t0:.1f}s",
                        flush=True,
                    )

    for bucket in range(num_buckets):
        out_files[bucket]["text"].close()
        out_files[bucket]["bin"].close()

    print(
        f"done lang {lang} lines read: {lines_read:,}, unique:{len(seen):,}, t={time() - t0:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    num_cpus = mp.cpu_count()
    with mp.Pool(num_cpus) as pool:
        pool.map(go, CCMATRIX_LANGS)
