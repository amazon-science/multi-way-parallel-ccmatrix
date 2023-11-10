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
import pickle
import statistics
import time
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotting_utils
from utils import (
    marginscore_with_len_analysis_list,
    num_translations_cutoffs,
    plots_dir,
    stats_dir,
    translation_bin_labels,
)

t0 = time.time()

res_dir = plots_dir

with open(f"{stats_dir}/marginscore_stats.pkl", "rb") as fr:
    ms_sums = pickle.load(fr)

with open(f"{stats_dir}/stats.pkl", "rb") as fr:
    stats = pickle.load(fr)

numrows_per_lang_per_bin = stats["numrows_per_lang_per_bin"]  # for calculating averages
langcounts = stats["count"]
sorted_langs = [x[0] for x in langcounts.most_common()]


translation_bins = list(range(len(num_translations_cutoffs) + 1))

# get matrix for heatmap

result = np.zeros(shape=(len(sorted_langs), len(translation_bins)), dtype=np.float32)
for ii, lang in enumerate(sorted_langs):
    for jj, bin_ in enumerate(translation_bins):
        result[ii][jj] = ms_sums[lang][bin_] / numrows_per_lang_per_bin[lang][bin_]

plotting_utils.plot_heatmap(
    result=result,
    savepath=f"{res_dir}/marginscore_heatmap.png",
    xticklabels=translation_bin_labels,
    yticklabels=sorted_langs,
    xlabel="# translations",
    title="Avg. margin score for all languages with varying #translations",
)


# Macro average for all langs
avg_across_langs = []
for bin_ in range(len(translation_bins)):
    avg = sum(result[:, bin_]) / len(result[:, bin_])
    avg_across_langs.append(avg)

plotting_utils.plot_barplot(
    y_vals=avg_across_langs,
    x_vals=translation_bins,
    save_dir=f"{res_dir}/marginscore_macroavg.png",
    xticks=translation_bin_labels,
    xlabel="# translations",
    ylabel="avg margin score",
    title="Macro average by lang of margin score by for varying # translations",
    ybottom=1.07,
    ytop=1.11,
)


# weighted average
total_count = 0
for ii, lang in enumerate(sorted_langs):
    total_count += langcounts[lang]

weighted_avg = np.zeros(
    (
        len(
            translation_bins,
        )
    )
)
for jj in range(len(translation_bins)):
    for ii, lang in enumerate(sorted_langs):
        weighted_avg[jj] += result[ii][jj] * langcounts[lang]

weighted_avg /= total_count

plotting_utils.plot_barplot(
    y_vals=weighted_avg,
    x_vals=translation_bins,
    save_dir=f"{res_dir}/marginscore_weightedavg.png",
    xticks=translation_bin_labels,
    xlabel="# translations",
    ylabel="avg margin score",
    title="Weighted average by lang of margin score by for varying # translations",
    ybottom=1.08,
    ytop=1.11,
)


# check trend for individual languages
lang_to_row = {}
for lang in sorted_langs:
    lang_to_row[lang] = len(lang_to_row)

for lang in ["en", "wo"]:
    row = lang_to_row[lang]
    if lang == "en":
        plotting_utils.plot_barplot(
            y_vals=result[row],
            x_vals=translation_bins,
            save_dir=f"{res_dir}/marginscore_{lang}.png",
            xticks=translation_bin_labels,
            xlabel="# translations",
            ylabel="avg margin score",
            title=f"Average margin score for {lang} by for varying # translations",
            ybottom=1.08,
            ytop=1.11,
        )
    if lang == "wo":
        plotting_utils.plot_barplot(
            y_vals=result[row],
            x_vals=translation_bins,
            save_dir=f"{res_dir}/marginscore_{lang}.png",
            xticks=translation_bin_labels,
            xlabel="# translations",
            ylabel="avg margin score",
            title=f"Average margin score for {lang} by for varying # translations",
            ybottom=1.06,
            ytop=1.11,
        )


# Which languages have a higher margin score on average?
ms_per_lang_num = Counter()
ms_per_lang_denom = Counter()

for ii, lang in enumerate(sorted_langs):
    for jj, bin_ in enumerate(translation_bins):
        ms_per_lang_num[lang] += ms_sums[lang][bin_]
        ms_per_lang_denom[lang] += numrows_per_lang_per_bin[lang][bin_]
ms_avg_per_lang = [
    ms_per_lang_num[lang] / ms_per_lang_denom[lang] for lang in sorted_langs
]

plotting_utils.plot_barplot(
    y_vals=ms_avg_per_lang,
    x_vals=sorted_langs,
    save_dir=f"{res_dir}/marginscore_perlang.png",
    xticks=sorted_langs,
    ylabel="avg margin score",
    title="Average margin score by language",
    ybottom=1.07,
    ytop=1.12,
    figsize=(20, 8),
)

print(f"Generated margin score plots (without length normalisation)")


# Length normalised analysis


# load len_bin_edges for the corresponding lang
def assign_bin(length, len_bin_edges):  # for a given sentence length, assign the bin
    for ii in range(1, len(len_bin_edges)):
        if length > len_bin_edges[ii - 1] and length <= len_bin_edges[ii]:
            return ii - 1


def process_bucket(bucket):
    print(f"Processing bucket {bucket}")

    score_lenbin = {}

    scores_lens_list = ms_len_list_per_bin[bucket]

    for score_len in scores_lens_list:
        score, length = score_len[0], score_len[1]

        sen_bin = assign_bin(length, len_bin_edges)

        if sen_bin not in score_lenbin:
            score_lenbin[sen_bin] = []

        score_lenbin[sen_bin].append(score)

    x_vals = list(score_lenbin.keys())
    x_vals.sort()

    # For mean
    y_vals_mean = [statistics.mean(score_lenbin[x]) for x in x_vals]

    # For median
    y_vals_median = [statistics.median(score_lenbin[x]) for x in x_vals]

    print(f"Completed bucket {bucket}")

    return (y_vals_mean, y_vals_median)


# Plot means
def plot_vals_list(vals):
    for label, val in zip(translation_bin_labels, vals):
        plt.scatter(x_labels, val, marker="x")
        plt.plot(x_labels, val[0], label=label)

    plt.xlabel("Sentence Length (chars)")
    plt.ylabel("Mean Margin Score")
    plt.title(
        f"Mean margin score vs sentence length category for different # translation buckets ({inp_lang})"
    )
    plt.legend()
    plt.savefig(f"{res_dir}/{inp_lang}_ms_len_mean.png")


for inp_lang in marginscore_with_len_analysis_list:
    # load dictionary with margin score & length for that language
    with open(f"{stats_dir}/marginscore_with_len_{inp_lang}.pkl", "rb") as fr:
        ms_len_dict = pickle.load(fr)

    ms_len_list_per_bin = ms_len_dict[inp_lang]

    # Compute bin edges for sentence length plots
    if inp_lang == "en":  # precalculated edges
        len_bin_edges = [0.0, 39.0, 59.0, 90.0, 140.0, 500.0]
    elif inp_lang == "es":
        len_bin_edges = [0.0, 39.0, 58.0, 87.0, 145.0, 500.0]
    elif inp_lang == "fr":
        len_bin_edges = [0.0, 38.0, 55.0, 80.0, 134.0, 500.0]
    elif inp_lang == "de":
        len_bin_edges = [0.0, 39.0, 58.0, 84.0, 133.0, 500.0]
    elif inp_lang == "pt":
        len_bin_edges = [0.0, 36.0, 53.0, 77.0, 128.0, 500.0]
    elif inp_lang == "it":
        len_bin_edges = [0.0, 38.0, 56.0, 84.0, 139.0, 500.0]
    elif inp_lang == "ru":
        len_bin_edges = [0.0, 35.0, 52.0, 76.0, 122.0, 500.0]
    elif inp_lang == "zh":
        len_bin_edges = [0.0, 11.0, 15.0, 22.0, 36.0, 500.0]
    else:
        all_lens = []
        for bin_ in ms_len_list_per_bin:
            for elem in ms_len_list_per_bin[
                bin_
            ]:  # contains tuples of margin score, length
                all_lens.append(elem[1])
        all_lens.sort()

        # char_dist = ms_len_dict['chars']
        # all_lens = []
        # all_keys = list(char_dist.keys())
        # all_keys.sort()
        # for key in all_keys:
        #     count = char_dist[key]
        #     all_lens += [key]*count

        res = pd.qcut(all_lens, 5, retbins=True)
        len_bin_edges = res[1]
        len_bin_edges[0] = 0  # lower bound for lengths

    print(f"Computed len bin edges for {inp_lang}: {len_bin_edges}")

    x_labels = []  # labels for plots with sentence length bins on x-axis
    for ii in range(1, len(len_bin_edges)):
        x_labels.append(f"({int(len_bin_edges[ii-1])}, {int(len_bin_edges[ii])}]")

    num_cpus = mp.cpu_count()

    all_buckets = list(ms_len_list_per_bin.keys())
    all_buckets.sort()

    with mp.Pool(num_cpus) as pool:
        vals = pool.map(process_bucket, all_buckets)
        means_list = []
        medians_list = []

        for val in vals:
            means_list.append(val[0])
            medians_list.append(val[1])

    # Plot means
    plotting_utils.plot_list(
        vals_list=means_list,
        labels_list=translation_bin_labels,
        x_ticks=x_labels,
        x_label="Sentence Length (chars)",
        y_label="Mean Margin Score",
        title=f"Mean margin score vs sentence length category for different # translation buckets ({inp_lang})",
        save_dir=f"{res_dir}/marginscore_mean_len_{inp_lang}.png",
        figsize=(8, 6),
    )

    # Plot medians
    plotting_utils.plot_list(
        vals_list=medians_list,
        labels_list=translation_bin_labels,
        x_ticks=x_labels,
        x_label="Sentence Length (chars)",
        y_label="Median Margin Score",
        title=f"Median margin score vs sentence length category for different # translation buckets ({inp_lang})",
        save_dir=f"{res_dir}/marginscore_median_len_{inp_lang}.png",
        figsize=(8, 6),
    )


print(f"Generated all plots in {time.time()-t0}s")
