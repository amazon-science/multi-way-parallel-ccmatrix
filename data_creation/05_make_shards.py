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
Processes files in hash2sent/ and saves final table as gzipped shards with one json line per entry.
"""
import gzip
import json
import multiprocessing as mp
import os
import pathlib
import sys
from collections import defaultdict
from time import time

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANGS
from config import TESTING, num_buckets, shard_dir
from utils import entry_to_row_score, myhash2int

pathlib.Path(shard_dir).mkdir(parents=True, exist_ok=True)


def go(bucket_number):
    t0 = time()
    main_table = defaultdict(dict)
    # 800s to read in, done at about 3000s
    # 2.5Gb memory
    # output file: ~2.9G
    print(f"starting bucket{bucket_number:03}", flush=True)
    for ii_lang, lang in enumerate(CCMATRIX_LANGS):
        print(
            f"processing bucket{bucket_number:03}, lang {lang} ({ii_lang}/{len(CCMATRIX_LANGS)}), t={time() - t0:.1f}s",
            flush=True,
        )
        fname_text = f"hash2sent/bucket{bucket_number:03}/hash2sent_{lang}.txt.gz"
        fname_bin = f"hash2sent/bucket{bucket_number:03}/hash2sent_{lang}.bin"

        num_to_read = os.stat(fname_bin).st_size // 16

        with gzip.open(fname_text, "rt") as fh_text, open(fname_bin, "rb") as fh_bin:
            lines_read = 0
            while True:
                line = fh_text.readline().replace("\n", " ").replace("\t", " ").strip()
                _ = fh_bin.read(8)  # dont need hash
                entry = fh_bin.read(8)
                if not entry:
                    break  # end of file

                row, bin_score = entry_to_row_score(myhash2int(entry))

                if lines_read % 1_000_000 == 0:
                    print(
                        f"read and processed {lines_read:,}/{num_to_read:,} lines of bucket{bucket_number:03}::{lang} files, t={time() - t0:.1f}s",
                        flush=True,
                    )

                lines_read += 1

                if lang in main_table[row]:
                    current_line, current_bin_score = main_table[row][lang]
                    if bin_score > current_bin_score:
                        # replace
                        main_table[row][lang] = (line, bin_score)
                else:
                    # add new entry
                    main_table[row][lang] = (line, bin_score)

    rows = 0
    sents = 0
    with gzip.open(
        f'{shard_dir}/bucket{bucket_number:03}{"_test" if TESTING else ""}.json.gz',
        "wt",
    ) as fout:
        for iix, row in enumerate(main_table):
            rows += 1
            with_scores = main_table[row]
            without_scores = {lang: with_scores[lang][0] for lang in with_scores}
            sents += len(without_scores)
            # fout.write(json.dumps(without_scores) + '\n')
            fout.write(json.dumps(with_scores) + "\n")
            if iix % 100_000 == 0:
                print(
                    f"wrote {iix:,} of {len(main_table):,} lines of bucket{bucket_number:03}, t={time() - t0:.1f}s",
                    flush=True,
                )

            if iix == 100_000 and TESTING:
                break

    print(
        f"done bucket{bucket_number:03}. rows: {rows:,}, sents: {sents:,}, t={time() - t0:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    num_threads = 20  # memory constrained, not cpu (each takes about 25Gb)
    with mp.Pool(num_threads) as pool:
        pool.map(go, range(num_buckets))
