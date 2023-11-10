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
import os
import random
from collections import Counter
from pprint import pprint

from utils import width_ranges, subset_data_dir, bitex_data_dir

random.seed(42)


def compute_length(src_sent, tgt_sent):
    return len(src_sent.strip()) + len(tgt_sent.strip())  # sum src/tgt, char len


def bin_edges_from_counter(counter, num_bins=20):
    values = [x for x in counter]
    values.sort()

    low = values[0]
    high = values[-1]
    num_values = sum([counter[x] for x in counter])

    used = 0
    used_edges = [0, ]
    bin_edges = [low, ]
    for val in values:
        count = counter[val]
        used += count
        # re-balance after potentially large bin(s)
        top = (used-used_edges[-1])/(num_values-used_edges[-1])
        bottom = 1/(num_bins - len(bin_edges) + 1)
        if top > bottom:
            bin_edges.append(val+1)
            used_edges.append(used)
            if len(bin_edges) == num_bins:
                bin_edges.append(high+1)
                used_edges.append(num_values)
                break

    return bin_edges


def main():
    parser = argparse.ArgumentParser('extract data subsets')
    parser.add_argument('src_lang')
    parser.add_argument('tgt_lang')
    args = parser.parse_args()
    widths = os.path.join(bitex_data_dir, f'{args.src_lang}_{args.tgt_lang}.width')
    src = os.path.join(bitex_data_dir, f'{args.src_lang}_{args.tgt_lang}.{args.src_lang}')
    tgt = os.path.join(bitex_data_dir, f'{args.src_lang}_{args.tgt_lang}.{args.tgt_lang}')

    # ###################  get equal sized none / low / med / high multi-way parallel
    # break into 4 parts
    # truncate each part to be the same length (chars) as shortest part

    char_counts = Counter()

    for width, src_sent, tgt_sent in zip(open(widths), open(src), open(tgt)):
        width = int(width)

        for start, end in width_ranges:
            if start <= width < end:
                char_counts[(start, end)] += compute_length(src_sent, tgt_sent)

    pprint(char_counts)

    min_char_count = min(char_counts.values())

    for start, end in width_ranges:
        char_count = 0
        base = os.path.join(subset_data_dir, f'{args.src_lang}_{args.tgt_lang}_start{start}_end{end}_origlen{char_counts[(start,end)]}_caplen{min_char_count}')
        with open(f'{base}.{args.src_lang}', 'wt') as src_out, open(f'{base}.{args.tgt_lang}', 'wt') as tgt_out:
            for width, src_sent, tgt_sent in zip(open(widths), open(src), open(tgt)):
                width = int(width)
                if start <= width < end:
                    char_count += compute_length(src_sent, tgt_sent)
                    if char_count > min_char_count:
                        break
                    src_out.write(src_sent)
                    tgt_out.write(tgt_sent)

    # ###################  get subsample of all that is length matched to width==2

    width2_len_count = Counter()
    all_len_count = Counter()
    for width, src_sent, tgt_sent in zip(open(widths), open(src), open(tgt)):
        width = int(width)
        src_tgt_len = compute_length(src_sent, tgt_sent)
        all_len_count[src_tgt_len] += 1
        if width == 2:
            width2_len_count[src_tgt_len] += 1

    # calculate sampling ratios to normalize all to length match width2
    length_bin_edges = bin_edges_from_counter(all_len_count)
    sample_ratios = dict()
    for start, end in zip(length_bin_edges, length_bin_edges[1:]):
        all_count = 0
        width2_count = 0
        for lenx in all_len_count:
            if start <= lenx < end:
                all_count += all_len_count[lenx]
                width2_count += width2_len_count[lenx]

        sample_ratios[(start, end)] = width2_count/all_count

    pprint(sample_ratios)

    def get_sample_ratio(lenx):
        for start, end in zip(length_bin_edges, length_bin_edges[1:]):
            if start <= lenx < end:
                sample_ratio = sample_ratios[(start, end)]
                return sample_ratio
        raise Exception(f'lenx={lenx}, length_bin_edges={length_bin_edges}')

    char_count = 0
    base = os.path.join(subset_data_dir, f'{args.src_lang}_{args.tgt_lang}_allLenMatch2_caplen{min_char_count}')
    with open(f'{base}.{args.src_lang}', 'wt') as src_out, open(f'{base}.{args.tgt_lang}', 'wt') as tgt_out:
        for width, src_sent, tgt_sent in zip(open(widths), open(src), open(tgt)):
            width = int(width)
            lenx = compute_length(src_sent, tgt_sent)
            if random.random() < get_sample_ratio(lenx):
                char_count += lenx
                if char_count > min_char_count:
                    break
                src_out.write(src_sent)
                tgt_out.write(tgt_sent)

    # ###################  get subsample of all that is not length matched

    char_count = 0
    base = os.path.join(subset_data_dir, f'{args.src_lang}_{args.tgt_lang}_all_caplen{min_char_count}')
    with open(f'{base}.{args.src_lang}', 'wt') as src_out, open(f'{base}.{args.tgt_lang}', 'wt') as tgt_out:
        for _, src_sent, tgt_sent in zip(open(widths), open(src), open(tgt)):
            lenx = compute_length(src_sent, tgt_sent)
            char_count += lenx
            if char_count > min_char_count:
                break
            src_out.write(src_sent)
            tgt_out.write(tgt_sent)

    # ###################  use as a data filter

    for _, end in width_ranges:
        base = os.path.join(subset_data_dir, f'{args.src_lang}_{args.tgt_lang}_dataFiltNumTranslations_lt{end}')
        with open(f'{base}.{args.src_lang}', 'wt') as src_out, open(f'{base}.{args.tgt_lang}', 'wt') as tgt_out:
            for width, src_sent, tgt_sent in zip(open(widths), open(src), open(tgt)):
                width = int(width)
                if width < end:
                    src_out.write(src_sent)
                    tgt_out.write(tgt_sent)


if __name__ == '__main__':
    main()
