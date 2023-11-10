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


import argparse
import gzip
import hashlib
import json
import multiprocessing as mp
import os
import random
import tempfile
from glob import glob
from time import time

from utils import num_buckets, local_table_shards_dir, bitex_data_dir


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Extract and shuffle parallel data for a set of (one or more) languages')
    parser.add_argument('--langs', type=str, nargs='+', required=True)
    parser.add_argument('--num_shards', default=512, type=int, help='decrease if get "too many open files" error')
    args = parser.parse_args()

    langs = args.langs  # TODO check to make sure these are actually lang codes

    num_shards = args.num_shards

    random.seed(42)

    def sent_tuple_to_shard(sents):
        bytes_in = ('X'.join(sents)).encode()
        hashobj = hashlib.sha256(bytes_in)
        val = int.from_bytes(hashobj.digest(), 'big')
        shard = val % num_shards
        assert 0 <= shard < num_shards  # not c-style remainder
        return shard


    tdir = tempfile.mkdtemp()

    def part0(bucket_num):
        """
        Extract desired sentence tuples from a given bucket, save sentence tuple + shard (based on hash) + width
        """
        bb = os.path.join(local_table_shards_dir, f'bucket{bucket_num:03}.json.gz')

        sent_tuple_count = 0
        total_line_count = 0
        t0 = time()

        with open(os.path.join(tdir, f'part0_bucket{bucket_num:03}'), 'wt') as fout:
            for ii, line in enumerate(gzip.open(bb, 'rt')):
                line2 = json.loads(line)
                total_line_count += 1
                if all([lang in line2 for lang in langs]):
                    sent_tuple_count += 1
                    sents = [line2[lang][0].replace('\n', '') for lang in langs]
                    width = len(line2)
                    shard = sent_tuple_to_shard(sents)
                    writeme = '\n'.join(sents) + f'\n{shard}\n{width}\n'
                    fout.write(writeme)

                if ii % 1_000_000 == 0:
                    print(f'bucket {bucket_num + 1}/{num_buckets}, lines: {ii:,}, '
                          f'correct_langs={sent_tuple_count:,}/{total_line_count:,}, t={time() - t0:.1f}s', flush=True)

        print(f'bucket sent_tuple_count={sent_tuple_count:,}, '
              f'total_line_count={total_line_count:,}, t={time() - t0:.1f}s', flush=True)


    def part1():
        """
        Write each sentence from each file in part0 to the desired output shard
        """
        part0_files = glob(os.path.join(tdir, 'part0*'))
        part0_files.sort()
        fouts = [open(os.path.join(tdir, f'part1_shard{ii:03}'), 'wt') for ii in range(num_shards)]
        for part1_file in part0_files:
            print('processing', part1_file, flush=True)
            with open(part1_file, 'rt') as fin:
                while True:
                    sents = []
                    for _ in range(len(langs)):
                        sent = fin.readline().replace('\n', '')
                        sents.append(sent)
                    shard = fin.readline().replace('\n', '')
                    width = fin.readline().replace('\n', '')

                    if width == '':
                        break
                    shard = int(shard.strip())
                    writeme = '\n'.join(sents)+f'\n{width}\n'
                    fouts[shard].write(writeme)

        for fout in fouts:
            fout.close()


    def part2():
        """
        Read in each shard, shuffle it, and append it to final output file
        """
        part1_files = glob(os.path.join(tdir, 'part1*'))
        part1_files.sort()

        base = os.path.join(bitex_data_dir, '_'.join(langs))
        out_files = [open(f'{base}.{lang}', 'wt') for lang in langs]
        with open(f'{base}.width', 'wt') as width_out:
            for part2_file in part1_files:
                print('processing', part2_file, flush=True)
                lines = []
                with open(part2_file, 'rt') as fin:
                    while True:
                        sents = []
                        for _ in range(len(langs)):
                            sents.append(fin.readline())
                        width = fin.readline()
                        if width == '':
                            break

                        lines.append(tuple(sents + [width, ]))

                random.shuffle(lines)

                for stuff in lines:
                    for ii in range(len(langs)):
                        sent = stuff[ii]
                        out_files[ii].write(sent)
                    width = stuff[len(langs)]
                    width_out.write(width)

        for ff in out_files:
            ff.close()

    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(part0, range(num_buckets))  # en-fr: 15min

    part1()  # en-fr: 7min
    part2()  # en-fr: 9min
