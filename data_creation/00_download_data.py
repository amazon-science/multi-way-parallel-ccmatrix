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
Script for downloading data for all language pairs from https://data.statmt.org/cc-matrix/
The data (849GB) is saved in the local directory raw_data/ and takes ~2.5 hrs to run on an i4i.32xlarge instance
"""

import multiprocessing as mp
import os.path
import pathlib
import subprocess as sp
import sys
from time import time

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANG_PAIRS
from config import TESTING, exclude_num, gz_dir


def download(lang_pair):
    lang0, lang1 = lang_pair.split("-")  # in alphabetical order
    print("langs:", lang0, lang1, flush=True)
    pathlib.Path(gz_dir).mkdir(parents=True, exist_ok=True)

    gz_file = f"{gz_dir}/{lang0}-{lang1}.tsv.gz"
    if os.path.isfile(gz_file):
        print(f"using already downloaded {gz_file}", flush=True)
    else:
        print("downloading data", flush=True)
        t0 = time()
        sp.check_call(
            f"wget --progress=bar:force:noscroll https://data.statmt.org/cc-matrix/{lang0}-{lang1}.bitextf.tsv.gz -O {gz_file}.part",
            shell=True,
        )
        sp.check_call(f"mv {gz_file}.part {gz_file}", shell=True)
        t1 = time()
        print(f"downloaded {gz_file} in {t1 - t0:.1f}s", flush=True)


if __name__ == "__main__":
    lang_pairs = CCMATRIX_LANG_PAIRS
    if TESTING:  # if testing, exlude some higher resource language pairs
        lang_pairs = lang_pairs[exclude_num:]

    num_cpus = mp.cpu_count()

    print(f"num language pairs: {len(lang_pairs)}, num cpus: {num_cpus}", flush=True)

    with mp.Pool(num_cpus) as pool:
        pool.map(download, lang_pairs)
