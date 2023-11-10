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
from evaluate import load

res_dir = "./ppl_plots"

if not os.path.exists(res_dir):
    os.makedirs(res_dir)


dataset = load_dataset("RicardoRei/wmt-mqm-human-evaluation", split="train")

df = dataset.to_pandas()  # just to make it easier to process

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
]

perplexity = load("perplexity", module_type="measurement")


def assign_bin(length, len_bin_edges):  # for a given sentence length, assign the bin
    if length == 0:  # will never happen
        return 0
    for ii in range(1, len(len_bin_edges)):
        if length > len_bin_edges[ii - 1] and length <= len_bin_edges[ii]:
            return ii - 1
    return ii - 1


for inp_lp in Counter(dataset["lp"]).keys():
    print(f"Starting {inp_lp}")

    df_lp = df[(df["lp"] == inp_lp) & (~df["system"].isin(remove_systems))]

    # source sentence lengths
    src_lens_cp = [len(x) for x in df_lp["src"]]
    src_sens_cp = list(df_lp["src"])
    mt_sens_cp = list(df_lp["mt"])
    ref_sens_cp = list(df_lp["ref"])

    # remove all Nones
    src_lens = []
    src_sens = []
    mt_sens = []
    ref_sens = []

    for ii in range(len(src_lens_cp)):
        if (
            src_lens_cp[ii] == None
            or src_sens_cp[ii] == None
            or mt_sens_cp[ii] == None
            or ref_sens_cp[ii] == None
        ):
            continue
        src_lens.append(src_lens_cp[ii])
        src_sens.append(src_sens_cp[ii])
        mt_sens.append(mt_sens_cp[ii])
        ref_sens.append(ref_sens_cp[ii])

    all_lens = sorted(src_lens)
    res = pd.qcut(all_lens, 10, retbins=True)
    # res = pd.qcut(range(all_lens[-1]+1), 10, retbins=True)
    len_bin_edges = res[1]
    len_bin_edges[0] = 0  # lower bound for lengths

    x_labels = []
    for ii in range(1, len(len_bin_edges)):
        x_labels.append(f"({int(len_bin_edges[ii-1])}, {int(len_bin_edges[ii])}]")

    src_len_bins = [assign_bin(x, len_bin_edges) for x in src_lens]

    ppl_mt = perplexity.compute(data=mt_sens, model_id="gpt2")  # for english

    ppl_ref = perplexity.compute(data=ref_sens, model_id="gpt2")  # for english

    print(f"Computed ppl for mt and src")

    with open(f"{res_dir}/ppl_mt_{inp_lp}.pkl", "wb") as fw:
        pickle.dump(ppl_mt, fw)

    with open(f"{res_dir}/ppl_ref_{inp_lp}.pkl", "wb") as fw:
        pickle.dump(ppl_ref, fw)

    ppl_per_len_bin_mt = {}
    ppl_per_len_bin_ref = {}

    for ii, len_bin in enumerate(src_len_bins):
        if len_bin not in ppl_per_len_bin_mt:
            ppl_per_len_bin_mt[len_bin] = []

        if len_bin not in ppl_per_len_bin_ref:
            ppl_per_len_bin_ref[len_bin] = []

        ppl_per_len_bin_mt[len_bin].append(ppl_mt["perplexities"][ii])
        ppl_per_len_bin_ref[len_bin].append(ppl_ref["perplexities"][ii])

    # plot mean and median
    x_vals = list(ppl_per_len_bin_mt.keys())  # all len bins
    x_vals.sort()

    y_vals_mt = [statistics.mean(ppl_per_len_bin_mt[bin_]) for bin_ in x_vals]
    y_vals_ref = [statistics.mean(ppl_per_len_bin_ref[bin_]) for bin_ in x_vals]

    plt.figure(figsize=(10, 10))

    plt.scatter(x_vals, y_vals_mt, marker="x")
    plt.plot(
        x_vals,
        y_vals_mt,
        label="Machine Translation",
    )

    plt.scatter(x_vals, y_vals_ref, marker="x")
    plt.plot(
        x_vals,
        y_vals_ref,
        label="Human Translation",
    )

    plt.xticks(x_vals, x_labels, rotation=90)

    plt.xlabel("Source Sentence Length Bin")
    plt.ylabel("Average laser cosine similarity")
    plt.title(f"Laser cosine similarity vs Sentence Lengths for {inp_lp}")
    plt.legend()
    plt.savefig(f"./{res_dir}/wmt_{inp_lp}_ppl.png")
    print(f"Saved plot for {inp_lp}")
