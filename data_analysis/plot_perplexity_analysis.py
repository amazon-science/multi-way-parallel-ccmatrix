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


import multiprocessing as mp
import os
import pickle
import statistics
import time
from collections import Counter

import pandas as pd
import plotting_utils
from utils import (
    num_samples_for_perplexity,
    num_translations_cutoffs,
    plots_dir,
    sample_lang,
    sampled_sens_dir,
    stats_dir,
    translation_bin_labels,
)

t0 = time.time()

if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

# get the distribution of sentence lengths (in characters)
all_lens = []
for bin_ in range(len(num_translations_cutoffs) + 1):
    fname = os.path.join(
        sampled_sens_dir, f"sens_per_bin_sampled_{sample_lang}_{bin_}.pkl"
    )
    with open(fname, "rb") as fr:
        sens = pickle.load(fr)
    for sen in sens:
        all_lens.append(len(sen))

# create sen len cutoffs
all_lens.sort()
res = pd.qcut(all_lens, 5, retbins=True)
len_bin_edges = res[1]
len_bin_edges[0] = 0  # lower bound for lengths

print(f"Computed len bin edges: {len_bin_edges}")


def assign_bin(length, len_bin_edges):  # for a given sentence length, assign the bin
    for ii in range(1, len(len_bin_edges)):
        if length > len_bin_edges[ii - 1] and length <= len_bin_edges[ii]:
            return ii - 1


# load results
with open(f"{stats_dir}/ppl_res_all_{sample_lang}.pkl", "rb") as fr:
    all_res = pickle.load(fr)

# Plot mean perplexity distribution (without length normalisation)
x_vals = list(all_res.keys())
x_vals.sort()
y_vals = [all_res[x]["mean_perplexity"] for x in x_vals]

plotting_utils.plot_barplot(
    x_vals=x_vals,
    y_vals=y_vals,
    save_dir=f"./{plots_dir}/ppl_{sample_lang}.png",
    xticks=translation_bin_labels,
    xlabel="Num Translations",
    ylabel="Avg. perplexity",
    title=f"Avg perplexity vs num translations for {num_samples_for_perplexity} sentences from each bin ({sample_lang})",
    figsize=(7, 5),
    ybottom=150,
)

# Plot length normalised perplexity
x_labels_len = []
for ii in range(1, len(len_bin_edges)):
    x_labels_len.append(f"({int(len_bin_edges[ii-1])}, {int(len_bin_edges[ii])}]")


def get_mean_median_count_per_bucket(bucket):
    print(f"Processing bucket {bucket}")

    ppl_lenbin = {}  # list of perplexities in each length bin
    count_lenbin = Counter()  # number of examples in each length bin

    fname = os.path.join(
        sampled_sens_dir, f"sens_per_bin_sampled_{sample_lang}_{bucket}.pkl"
    )
    with open(fname, "rb") as fr:
        all_sens = pickle.load(fr)

    perplexities = all_res[bucket]["perplexities"]

    for sen, ppl in zip(all_sens, perplexities):
        sen_bin = assign_bin(len(sen), len_bin_edges)

        if sen_bin not in ppl_lenbin:
            ppl_lenbin[sen_bin] = []

        ppl_lenbin[sen_bin].append(ppl)
        count_lenbin[sen_bin] += 1

    x_vals = list(ppl_lenbin.keys())
    x_vals.sort()

    y_vals_mean = [statistics.mean(ppl_lenbin[x]) for x in x_vals]
    y_vals_median = [statistics.median(ppl_lenbin[x]) for x in x_vals]

    return y_vals_mean, y_vals_median, count_lenbin


num_cpus = mp.cpu_count()

with mp.Pool(num_cpus) as pool:
    vals = pool.map(get_mean_median_count_per_bucket, list(all_res.keys()))

    means_list = []
    medians_list = []
    counts_dist = []

    for ii, val in enumerate(vals):  # for each num translations bin
        means_list.append(val[0])
        medians_list.append(val[1])
        counts_dist.append(val[2])

# normalise counts_dist
counts_dist_normalised = []
for ii in range(len(all_res)):  # for each num translations bin
    normalised_dist = Counter()
    for sen_bin in range(len(x_labels_len)):  # for each sentence length bin
        normalised_dist[x_labels_len[sen_bin]] = (
            counts_dist[ii][sen_bin] / num_samples_for_perplexity
        )

    counts_dist_normalised.append(normalised_dist)

print(counts_dist_normalised)

# Plot means
plotting_utils.plot_list(
    vals_list=means_list,
    labels_list=translation_bin_labels,
    x_ticks=x_labels_len,
    x_label="Sentence Length (chars)",
    y_label="Mean Perplexity",
    title=f"Mean perplexity vs sentence length category for different # translation buckets ({sample_lang})",
    save_dir=f"{plots_dir}/ppl_mean_len_{sample_lang}.png",
    figsize=(8, 6),
)

# Plot means
plotting_utils.plot_list(
    vals_list=medians_list,
    labels_list=translation_bin_labels,
    x_ticks=x_labels_len,
    x_label="Sentence Length (chars)",
    y_label="Median Perplexity",
    title=f"Median perplexity vs sentence length category for different # translation buckets ({sample_lang})",
    save_dir=f"{plots_dir}/ppl_median_len_{sample_lang}.png",
    figsize=(8, 6),
)

# plot distribution of number of sentences from each sentence length bucket in different # translations buckets
df = pd.DataFrame(data=counts_dist_normalised, index=translation_bin_labels)
ax = df.plot(
    kind="bar",
    rot=90,
    xlabel="Num translations",
    ylabel="Fraction of documents",
    title="Fraction of documents in different sentence length bins for different # translations",
    stacked=False,
    figsize=(13, 8),
)
ax.legend(bbox_to_anchor=(1, 1))
fig = ax.get_figure()
fig.savefig(f"{plots_dir}/ppl_sentence_length_dist_{sample_lang}.png")


print(f"Generated all plots in {time.time()-t0}s")
