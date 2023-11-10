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
import time

from evaluate import load
from utils import (
    TESTING,
    num_translations_cutoffs,
    sample_lang,
    sampled_sens_dir,
    stats_dir,
)

res_dir = stats_dir

if not os.path.exists(res_dir):
    os.makedirs(res_dir)


def get_perplexity(bin_):
    print(f"Starting perplexity for bin {bin_}")
    start = time.time()

    with open(
        f"{sampled_sens_dir}/sens_per_bin_sampled_{sample_lang}_{bin_}.pkl", "rb"
    ) as fr:
        data = pickle.load(fr)

    if TESTING:
        data = data[:100]

    print(f"Loaded data for bin {bin_}")

    print(f"Measuring perplexity for {len(data)} sentences in bin {bin_}")

    results = perplexity.compute(data=data, model_id="gpt2")  # for english
    # results = perplexity.compute(data=data, model_id='bigscience/bloom-1b7') #for multilingual

    print(f"Finished bin {bin_} for {inp_lang} in {time.time()-start}s")
    return results


if __name__ == "__main__":
    t0 = time.time()

    perplexity = load("perplexity", module_type="measurement")

    inp_lang = sample_lang  # calculate perplexity for the lang that was sampled

    all_bins = list(range(len(num_translations_cutoffs) + 1))

    all_results = {}

    # Sequential
    for bin_ in all_bins:
        ppl = get_perplexity(bin_)
        all_results[bin_] = ppl

    # Parallel --> gives OOM
    # with mp.Pool(num_cpus) as pool:
    #     all_res = pool.map(get_perplexity, all_bins)

    with open(os.path.join(res_dir, f"ppl_res_all_{inp_lang}.pkl"), "wb") as fw:
        pickle.dump(all_results, fw)

    print(f"Code executed in {time.time() - t0}s")
