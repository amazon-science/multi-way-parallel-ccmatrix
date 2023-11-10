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


import matplotlib.pyplot as plt
import seaborn as sns


def plot_heatmap(
    result,
    savepath,
    xticklabels=None,
    yticklabels=None,
    xlabel=None,
    ylabel=None,
    title=None,
    figsize=(15, 25),
    cmap=plt.cm.Blues,
    linecolor="white",
):
    plt.figure(figsize=figsize)
    ax = sns.heatmap(
        result,
        annot=False,
        cmap=cmap,
        linewidths=0.5,
        xticklabels=xticklabels,
        yticklabels=yticklabels,
        linecolor=linecolor,
    )
    ax.set(xlabel=xlabel, title=title)
    plt.savefig(savepath)


def plot_barplot(
    x_vals,
    y_vals,
    save_dir,
    xticks=None,
    xlabel=None,
    ylabel=None,
    title=None,
    ybottom=None,
    ytop=None,
    figsize=None,
):
    plt.figure(figsize=figsize)

    plot = sns.barplot(y=y_vals, x=x_vals, color="cornflowerblue")

    if not xticks:  # if xticks are not specified, let them be x_vals
        xticks = x_vals
    plot.set_xticklabels(xticks)

    plot.set_ylim(bottom=ybottom, top=ytop)  # for adjusting the plot y axis range

    plot.set(xlabel=xlabel, ylabel=ylabel, title=title)
    plt.savefig(save_dir)


def plot_list(
    vals_list, labels_list, x_ticks, x_label, y_label, title, save_dir, figsize=None
):
    plt.figure(figsize=figsize)
    for label, val in zip(labels_list, vals_list):
        plt.scatter(x_ticks, val, marker="x")
        plt.plot(x_ticks, val, label=label)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend()
    plt.savefig(save_dir)
