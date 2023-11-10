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
import statistics
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
from datasets import load_dataset
from sklearn.metrics.pairwise import cosine_similarity

# load data from huggingface
dataset = load_dataset("RicardoRei/wmt-mqm-human-evaluation", split="train")

df = dataset.to_pandas()  # just to make it easier to process

print(f"Language pairs with counts in data: {Counter(dataset['lp'])}")

plot_save_dir = "./plots"

if not os.path.exists(plot_save_dir):
    os.makedirs(plot_save_dir)

remove_systems = [
    "Human-A.0",
    "Human-B.0",
    "Human-P.0",
    "ref-A",
    "ref-B",
    "ref-C",
    "ref-D",
    "ref.A",
    "ref.B",
    "refA",
    "refB",
]  # remove these systems from analysis


def assign_bin(length, len_bin_edges):  # for a given sentence length, assign the bin
    if length == 0:  # will never happen
        return 0
    for ii in range(1, len(len_bin_edges)):
        if length > len_bin_edges[ii - 1] and length <= len_bin_edges[ii]:
            return ii - 1
    return ii - 1


def plot_vals(x_vals, y_vals, x_ticks, xlabel, ylabel, title, save_path, figsize=None):
    save_path = os.path.join(plot_save_dir, save_path)

    plt.figure(figsize=figsize)
    plt.scatter(x_vals, y_vals, marker="x")
    plt.plot(x_vals, y_vals)
    plt.xticks(x_vals, x_ticks, rotation=90)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(save_path)


for inp_lp in Counter(dataset["lp"]).keys():
    df_lp = df[
        (df["lp"] == inp_lp) & (~df["system"].isin(remove_systems))
    ]  # select data rows from the input language pair and remove rows with system in 'remove_systems'

    # source sentence lengths
    src_lens = [len(x) for x in df_lp["src"]]

    # MQM scores
    scores = df_lp["score"]

    src_sens = df_lp["src"]
    mt_sens = df_lp["mt"]
    ref_sens = df_lp["ref"]

    # Create sentence length bins
    all_lens = sorted(src_lens)
    res = pd.qcut(
        all_lens, 10, retbins=True
    )  # for bins containing ~same amount of data
    # res = pd.qcut(range(all_lens[-1]+1), 10, retbins=True) #for equidistant bins
    len_bin_edges = res[1]
    len_bin_edges[0] = 0  # lower bound for lengths

    print(
        f"Created sentence length bin edges using source sentences from {inp_lp}. Edges: {len_bin_edges}"
    )

    src_len_bins = [
        assign_bin(x, len_bin_edges) for x in src_lens
    ]  # assign the sentence length bin to every source sentence

    x_labels = []  # x axis labels for plots
    for ii in range(1, len(len_bin_edges)):
        x_labels.append(f"({int(len_bin_edges[ii-1])}, {int(len_bin_edges[ii])}]")

    scores_per_len_bin = {}
    for ii, score in enumerate(scores):
        len_bin = src_len_bins[ii]
        len_ = src_lens[ii]
        if len_bin not in scores_per_len_bin:
            scores_per_len_bin[len_bin] = []
        scores_per_len_bin[len_bin].append(score)
        # scores_per_len_bin[len_bin].append(score/len_) #for length normalised scores

    # plot mean and median
    x_vals = list(scores_per_len_bin.keys())  # all len bins
    x_vals.sort()

    y_vals_mqm_mean = [statistics.mean(scores_per_len_bin[bin_]) for bin_ in x_vals]
    y_vals_mqm_median = [statistics.median(scores_per_len_bin[bin_]) for bin_ in x_vals]

    if inp_lp == "en-ru":  # since mqm scores follow opposite trend
        y_vals_mqm_mean = [-y for y in y_vals_mqm_mean]
        y_vals_mqm_median = [-y for y in y_vals_mqm_median]

    # mean
    plot_vals(
        x_vals,
        y_vals_mqm_mean,
        x_labels,
        xlabel="Source Sentence Length Bin",
        ylabel="Mean of length normalised MQM Score",
        title=f"Mean of length normalised MQM Score vs Sentence Length Bin for {inp_lp}",
        save_path=f"mean_mqm_len_{inp_lp}.png",
        figsize=(10, 10),
    )

    # median
    plot_vals(
        x_vals,
        y_vals_mqm_median,
        x_labels,
        xlabel="Source Sentence Length Bin",
        ylabel="Median of length normalised MQM Score",
        title=f"Median of length normalised MQM Score vs Sentence Length Bin for {inp_lp}",
        save_path=f"median_mqm_len_{inp_lp}.png",
        figsize=(10, 10),
    )

    print(f"Generated plots for MQM vs sentence length analysis for {inp_lp}")

    # Analysis of laser scores for mt vs ref with varying sentence lengths

    from laserembeddings import Laser

    laser = Laser()

    src_lang, trg_lang = inp_lp.split("-")

    # laser embedding for src sentences
    if os.path.exists(f"{inp_lp}_src_laser.pickle"):  # if precalculated
        print(f"Loading src embeddings")
        with open(f"{inp_lp}_src_laser.pickle", "rb") as fr:
            src_sen_embeddings = pickle.load(fr)
    else:  # else, calculate and save (takes ~40 min)
        print(f"Generating src embeddings")
        src_sen_embeddings = laser.embed_sentences(src_sens, lang=src_lang)
        with open(f"{inp_lp}_src_laser.pickle", "wb") as fw:
            pickle.dump(src_sen_embeddings, fw)

    # laser embedding for mt sentences
    if os.path.exists(f"{inp_lp}_mt_laser.pickle"):
        print(f"Loading mt embeddings")
        with open(f"{inp_lp}_mt_laser.pickle", "rb") as fr:
            mt_sen_embeddings = pickle.load(fr)
    else:
        print(f"Generating mt embeddings")
        mt_sen_embeddings = laser.embed_sentences(mt_sens, lang=trg_lang)
        with open(f"{inp_lp}_mt_laser.pickle", "wb") as fw:
            pickle.dump(mt_sen_embeddings, fw)

    # laser embedding for ref sentences
    if os.path.exists(f"{inp_lp}_ref_laser.pickle"):
        print(f"Loading ref embeddings")
        with open(f"{inp_lp}_ref_laser.pickle", "rb") as fr:
            ref_sen_embeddings = pickle.load(fr)
    else:
        print(f"Generating ref embeddings")
        ref_sen_embeddings = laser.embed_sentences(ref_sens, lang=trg_lang)
        with open(f"{inp_lp}_ref_laser.pickle", "wb") as fw:
            pickle.dump(ref_sen_embeddings, fw)

    print(f"Generated all laser embedding")

    src_mt_per_len_bin = (
        {}
    )  # cosine similarity of src and mt sentences per source sentence length bin
    src_ref_per_len_bin = (
        {}
    )  # cosine similarity of src and ref sentences per source sentence length bin

    for ii, len_bin in enumerate(src_len_bins):
        if len_bin not in src_mt_per_len_bin:
            src_mt_per_len_bin[len_bin] = []

        if len_bin not in src_ref_per_len_bin:
            src_ref_per_len_bin[len_bin] = []

        src_emb = src_sen_embeddings[ii]
        mt_emb = mt_sen_embeddings[ii]
        ref_emb = ref_sen_embeddings[ii]

        src_mt_per_len_bin[len_bin].append(
            cosine_similarity(src_emb.reshape(1, -1), mt_emb.reshape(1, -1))[0][0]
        )
        src_ref_per_len_bin[len_bin].append(
            cosine_similarity(src_emb.reshape(1, -1), ref_emb.reshape(1, -1))[0][0]
        )

    # Plot
    x_vals = list(src_mt_per_len_bin.keys())  # all len bins
    x_vals.sort()

    y_vals_mt = [statistics.mean(src_mt_per_len_bin[bin_]) for bin_ in x_vals]
    y_vals_ref = [statistics.mean(src_ref_per_len_bin[bin_]) for bin_ in x_vals]

    plt.figure(figsize=(10, 10))
    plt.scatter(x_vals, y_vals_mt, marker="x")
    plt.plot(
        x_vals,
        y_vals_mt,
        label="src-mt",
    )

    plt.scatter(x_vals, y_vals_ref, marker="x")
    plt.plot(
        x_vals,
        y_vals_ref,
        label="src-ref",
    )

    plt.xticks(x_vals, x_labels, rotation=90)

    plt.xlabel("Source Sentence Length Bin")
    plt.ylabel("Average laser cosine similarity")
    plt.title(
        f"Average laser cosine similarity for src-mt and src-ref {inp_lp} pairs across different sentence lengths"
    )
    plt.legend()
    plt.savefig(f"{plot_save_dir}/mean_laser_len_{inp_lp}.png")

    print(f"Generated laser plots for {inp_lp}")
