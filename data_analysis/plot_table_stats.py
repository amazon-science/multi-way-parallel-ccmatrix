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


import os
import pickle
import sys
import time
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotting_utils
import seaborn as sns
from utils import (
    find_bin,
    langcounts_file,
    num_translations_cutoffs,
    plots_dir,
    stats_dir,
    translation_bin_labels,
)

sys.path.append("../")

from ccmatrix_utils.ccmatrix_langpairs import CCMATRIX_LANGS

t0 = time.time()

if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

with open(f"{stats_dir}/stats.pkl", "rb") as fr:
    stats = pickle.load(fr)

# Number of rows and sentences in table
print(f"Number of rows in the table: {stats['row_count']}")
print(f"Number of sentences in the table: {stats['sent_count']}")

# Plot of count per language
sorted_langcounts = stats["count"].most_common()
x_vals = [x[0] for x in sorted_langcounts]
y_vals = [x[1] for x in sorted_langcounts]
plotting_utils.plot_barplot(
    x_vals=x_vals,
    y_vals=y_vals,
    save_dir=f"{plots_dir}/counts_per_lang.png",
    xticks=x_vals,
    ylabel="Sentences in table",
    title="Number of sentences for each language in the table",
    figsize=(20, 8),
)

# How much content is multiway parallel?
mway_count = stats["row_count"] - stats["width_hist"][2]  # number of multiway rows
print(f"Multiway rows: {round(mway_count*100/stats['row_count'],3)}%")

# most translated sentence
widths = list(stats["width_hist"].keys())
print(f"Max languages a sentence is translated in: {max(widths)}")

# plot width histogram
y_vals = np.zeros((len(num_translations_cutoffs) + 1))

widths.sort()
for width in widths:
    width_bin = find_bin(width)
    y_vals[width_bin] += stats["width_hist"][width]

y_vals = [y / stats["row_count"] for y in y_vals]

plotting_utils.plot_barplot(
    x_vals=translation_bin_labels,
    y_vals=y_vals,
    save_dir=f"./{plots_dir}/width_hist.png",
    xticks=translation_bin_labels,
    title="Fraction of Tuples vs Number of Translations",
    xlabel="Number of Translations",
    ylabel="Fraction of Tuples",
)

# Average row size
num = 0.0
for width in stats["width_hist"]:
    num += width * stats["width_hist"][width]
num /= stats["row_count"]

print(f"Average row size: {round(num, 3)}")

# Average row size excluding '2'
num = 0.0
total = 0
for width in stats["width_hist"]:
    if width == 2:
        continue
    num += width * stats["width_hist"][width]
    total += stats["width_hist"][width]
# num /= stats['row_count']
num /= total

print(f"Average row size: {round(num, 3)}")

# Average translations per language
avg_per_lang = Counter()
micro_num = 0.0
micro_den = 0.0
for lang in stats["width"]:
    avg_per_lang[lang] = stats["width"][lang] / stats["count"][lang]
    micro_num += stats["width"][lang]
    micro_den += stats["count"][lang]

# micro avg
print(
    f"Micro avg of number of translations per language: {round(micro_num/micro_den, 3)}"
)

# Macro avg
macro_avg = 0.0
for lang in avg_per_lang:
    macro_avg += avg_per_lang[lang]
macro_avg /= len(avg_per_lang)
print(f"Macro avg of number of translations per language: {round(macro_avg, 3)}")

# Weighted macro avg
with open(f"{langcounts_file}", "rb") as fr:
    lang_counts = pickle.load(fr)
lang_counts = Counter(lang_counts)

num = 0.0
den = 0.0
for lang in avg_per_lang:
    # num += avg_per_lang[lang] * lang_counts[lang] #for waeighing by count in ccmatrix data
    # den += lang_counts[lang]
    num += (
        avg_per_lang[lang] * stats["count"][lang]
    )  # for weighing by count in mway data
    den += stats["count"][lang]
print(f"Weighted macro avg of number of translations per language: {round(num/den,3)}")

# Averages for top n high and low resource langs
n = 10

topn = [x[0] for x in lang_counts.most_common()[:n]]
lown = [x[0] for x in lang_counts.most_common()[-n:]]


macro_avg = 0.0
for lang in topn:
    macro_avg += avg_per_lang[lang]
macro_avg /= len(topn)
print(f"Macro avg. for top {n} highest resource langs: {round(macro_avg, 3)}")

macro_avg = 0.0
for lang in lown:
    macro_avg += avg_per_lang[lang]
macro_avg /= len(lown)
print(f"Macro avg. for top {n} lowest resource langs: {round(macro_avg, 3)}")

# Plot average translations with counts


x_vals = [x[0] for x in lang_counts.most_common()]
# y_freqs = [np.log10(lang_counts[x]) for x in x_vals]
y_freqs = [np.log10(stats["count"][x]) for x in x_vals]
y_avg = [avg_per_lang[x] for x in x_vals]

df = pd.DataFrame(
    data={"avg. translations": y_avg, "log frequency": y_freqs}, index=x_vals
)
ax = df.plot(
    kind="bar",
    rot=0,
    title="Comparison of average translations for different languages",
    figsize=(20, 8),
    color=["royalblue", "lightgrey"],
    width=0.8,
)

ax2 = ax.twinx()
y1, y2 = ax.get_ylim()
ax2.set_ylim(y1, y2)

ax2.set_yticklabels([""] + [f"10^{int(x)}" for x in ax2.get_yticks()[1:]])

ax.set_ylabel("Avg. Translations")
# ax.tick_params('y', colors='royalblue')

ax2.set_ylabel("Frequency in Data")
# ax2.tick_params('y', colors='grey')

ax.set_xlabel("Language")


fig = ax.get_figure()
fig.savefig(f"{plots_dir}/lang_comparison.png")


# Sentence lengths analysis
len_per_lang = stats["len_per_lang_per_bin"]
numrows_per_lang = stats["numrows_per_lang_per_bin"]

sorted_langs = [x[0] for x in lang_counts.most_common()]

translation_bins = list(range(len(num_translations_cutoffs) + 1))


# get macro and weighted average of results
def macro_avg(result):
    # Macro average for all langs
    avg_across_langs = []
    for bin_ in range(len(translation_bins)):
        avg = sum(result[:, bin_]) / len(result[:, bin_])
        avg_across_langs.append(avg)
    return avg_across_langs


def weighted_avg(result):
    total_count = 0
    for ii, lang in enumerate(sorted_langs):
        # total_count += lang_counts[lang]
        total_count += stats["count"][lang]
    weighted_avg_nums = np.zeros(
        (
            len(
                translation_bins,
            )
        )
    )
    weighted_avg_nums = np.zeros(
        (
            len(
                translation_bins,
            )
        )
    )
    for jj in range(len(translation_bins)):
        for ii, lang in enumerate(sorted_langs):
            # weighted_avg_nums[jj] += result[ii][jj] * lang_counts[lang]
            weighted_avg_nums[jj] += result[ii][jj] * stats["count"][lang]
    weighted_avg_nums /= total_count

    return weighted_avg_nums


# Avg sentence length for all langs
result = np.zeros(shape=(len(sorted_langs), len(translation_bins)), dtype=np.float32)

for ii, lang in enumerate(sorted_langs):
    for jj, bin_ in enumerate(translation_bins):
        result[ii][jj] = len_per_lang[lang][bin_] / numrows_per_lang[lang][bin_]

plotting_utils.plot_heatmap(
    result,
    savepath=f"{plots_dir}/avg_sen_len.png",
    xticklabels=translation_bin_labels,
    yticklabels=sorted_langs,
    xlabel="# translations",
    title="Avg. sentence length for all languages with varying #translations",
)

sen_macro_avg = macro_avg(result)
plotting_utils.plot_barplot(
    y_vals=sen_macro_avg,
    x_vals=translation_bins,
    save_dir=f"{plots_dir}/avg_len_macro_avg.png",
    xticks=translation_bin_labels,
    xlabel="# translations",
    ylabel="avg sen length",
    title="Macro average of sen length by language with varying # translations",
    ybottom=60,
    ytop=80,
)  # note- ybottom and ytop have been set based on best values in previous runs, and can be changed based on the data value ranges


sen_weighted_avg = weighted_avg(result)
plotting_utils.plot_barplot(
    y_vals=sen_weighted_avg,
    x_vals=translation_bins,
    save_dir=f"{plots_dir}/avg_len_weighted_avg.png",
    xticks=translation_bin_labels,
    xlabel="# translations",
    ylabel="avg sen length",
    title="Weighted average of sen length by language with varying # translations",
    ybottom=50,
    ytop=90,
)


# P(lang1|lang2)


def plot_colormesh(
    result,
    xticks,
    yticks,
    x_tick_label,
    y_tick_label,
    xlabel,
    ylabel,
    title,
    figsize,
    save_dir,
):
    plt.figure()
    plt.rcParams["figure.figsize"] = figsize

    fig, ax = plt.subplots(1, 1)

    plt.pcolormesh(result, edgecolors="k", linewidth=1)
    ax = plt.gca()

    ax.set_xticks(xticks + 0.5)
    ax.set_yticks(yticks + 0.5)

    ax.set_xticklabels(x_tick_label)
    ax.set_yticklabels(y_tick_label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_title(title)

    plt.tight_layout()
    plt.savefig(save_dir, bbox_inches="tight")


# filter out langs with very few sentences
MIN = 1_000_000
langs_filtered = [x for x in CCMATRIX_LANGS if stats["count"][x] > MIN]
langs_sorted = sorted(langs_filtered, key=lambda x: stats["count"][x], reverse=True)

result = np.zeros(shape=(len(langs_sorted), len(langs_sorted)), dtype=np.float32)


for ii, lang_ii in enumerate(langs_sorted):
    for jj, lang_jj in enumerate(langs_sorted):
        if ii == jj:
            result[(ii, jj)] = 1.0
        else:
            langA, langB = sorted((lang_ii, lang_jj))
            result[(jj, ii)] = (
                stats["lp_counts"][(langA, langB)] / stats["count"][lang_ii]
            )

plot_colormesh(
    result=result,
    xticks=np.array(range(len(langs_sorted))),
    yticks=np.array(range(len(langs_sorted))),
    x_tick_label=langs_sorted,
    y_tick_label=langs_sorted,
    xlabel="langX",
    ylabel="langY",
    title="Heatmap of P(langY|langX)",
    save_dir=f"{plots_dir}/prob_l1_given_l2.png",
    figsize=(20, 12),
)

# plotting_utils.plot_heatmap(result=result, savepath=f"{plots_dir}/prob_l1_given_l2.png", xticklabels=langs_sorted, yticklabels=langs_sorted, cmap='viridis', figsize=(20,20), linecolor='black')

# P(lang3 | lang1, lang2)
N_lang_pairs = 200  # Number of language pairs to show in the plot (Max: 1197)

# find top language pairs
pair_counts = Counter()
for key in stats["lp_counts"]:
    if type(key) == type((1, 2)) and len(key) == 2:
        pair_counts[key] = stats["lp_counts"][key]

top_lps = [x for x, _ in pair_counts.most_common(N_lang_pairs)]
top_lps.reverse()  # for plot

result = np.zeros(shape=(len(top_lps), len(langs_sorted)), dtype=np.float32)

for ii, lp in enumerate(top_lps):
    for jj, lang in enumerate(langs_sorted):
        a, b, c = sorted((lp[0], lp[1], lang))
        A, B = sorted((lp[0], lp[1]))
        result[(ii, jj)] = stats["lp_counts"][(a, b, c)] / stats["lp_counts"][(A, B)]

plot_colormesh(
    result=result,
    xticks=np.array(range(len(langs_sorted))),
    yticks=np.array(range(len(top_lps))),
    x_tick_label=langs_sorted,
    y_tick_label=[f"{a}-{b}" for a, b in top_lps],
    xlabel="langZ",
    ylabel="langX-langY",
    title="Heatmap of P(langZ|langX, langY)",
    figsize=(20, 50),
    save_dir=f"{plots_dir}/prob_3lang.png",
)

# plotting_utils.plot_heatmap(result=result, savepath=f"{plots_dir}/prob_3lang.png", xticklabels=langs_sorted, yticklabels=[f'{a}-{b}' for a, b in top_lps], cmap='viridis', figsize=(20,30), linecolor='black')

print(f"Saved all plots in {time.time()-t0}s")




### alternate plots/lang_comparison.png

langs = []
counts = []
widths = []
for ii, (lang, count) in enumerate(stats['count'].most_common()):
    # alternate lines in legend
    langs.append(('\n' if ii%2 else '') + lang.title())
    counts.append(count)
    widths.append( stats['width'][lang] / count)


plt.rc('font', size=8)
plt.rc('axes', titlesize=14)
plt.rc('axes', labelsize=14)
plt.rc('xtick', labelsize=10)
plt.rc('ytick', labelsize=12)
plt.rc('legend', fontsize=8)
plt.rc('figure', titlesize=12)

xvals = range(len(langs))
 
fig, ax1 = plt.subplots(figsize=(16, 4)) 
 
color = 'tab:blue'
#ax1.set_xlabel('Language')

ax1.set_xticks(xvals)
ax1.set_xticklabels(langs)
ax1.set_xlim(-1, len(xvals))  # get rid of whitespace on each side
ax1.set_ylabel('Avg. Languages / Tuple', color = color) 
ax1.bar(xvals, widths, color = color, width=-0.4, align='edge')  #To align the bars on the right edge pass a negative width and align='edge' 
ax1.tick_params(axis ='y', labelcolor = color) 

ax2 = ax1.twinx() 
 
color = 'tab:grey'
ax2.set_ylabel('Total Sentences', color = color) 
ax2.bar(xvals, counts, color = color, width=0.4, align='edge')
ax2.tick_params(axis ='y', labelcolor = color) 
ax2.set_yscale('log')

plt.margins(x=0)
plt.savefig("plots/lang_comparison.png", pad_inches=0.02, bbox_inches='tight', dpi=300)
