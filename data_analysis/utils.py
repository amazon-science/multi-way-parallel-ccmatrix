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


TESTING = False

num_shards = 100  # number of table shards

num_translations_cutoffs = [2, 3, 4, 6, 10, 20]
translation_bin_labels = ["2", "3", "4", "[5,7)", "[7,10)", "[10,20)", "20+"]

import bisect


def find_bin(num_translations):
    """
    Find the bin corresponding to the number of translations
    """
    return bisect.bisect_left(num_translations_cutoffs, num_translations)


local_table_shards_dir = "../data_creation/shards"

stats_dir = "./stats"
plots_dir = "./plots"

toxicity_lists_dir = "./NLLB-200_TWL"  # dir containing unzipped toxicity lists

langcounts_file = "../ccmatrix_utils/ccmatrix_counts/lang_counts.pickle"  # file containing count of every language
paircounts_file = "../ccmatrix_utils/ccmatrix_counts/langpair_counts.pickle"

cutoffs_file = "../data_creation/cutoffs.txt"

with open(cutoffs_file, "r") as fr:
    cutoffs = fr.read().split("\n")
    cutoffs.pop()
    cutoffs = [float(x) for x in cutoffs]

bin_to_score_mapping = {}
for ii, cutoff in enumerate(cutoffs):
    bin_to_score_mapping[ii] = cutoff
bin_to_score_mapping[len(cutoffs)] = 1.25  # upper bound of last bin

marginscore_with_len_analysis_list = [
    "en"
]  # list of languages for which margin score with length analysis has to be done

num_samples_for_perplexity = 100_000
sampled_sens_dir = "./sampled_sens"
sample_lang = "en"  # the language to be sampled


# mapping between nllb and ccmatrix language codes
NLLB_CCMATRIX_MAPPING = {
    "afr_Latn": "af",
    "als_Latn": "sq",
    "amh_Ethi": "am",
    "arb_Arab": "ar",
    "ast_Latn": "ast",
    "azj_Latn": "az",
    "bel_Cyrl": "be",
    "ben_Beng": "bn",
    "bul_Cyrl": "bg",
    "cat_Latn": "ca",
    "ceb_Latn": "ceb",
    "ces_Latn": "cs",
    "cym_Latn": "cy",
    "dan_Latn": "da",
    "deu_Latn": "de",
    "ell_Grek": "el",
    "eng_Latn": "en",
    "epo_Latn": "eo",
    "est_Latn": "et",
    "fin_Latn": "fi",
    "fra_Latn": "fr",
    "gaz_Latn": "om",
    "gla_Latn": "gd",
    "gle_Latn": "ga",
    "glg_Latn": "gl",
    "hau_Latn": "ha",
    "heb_Hebr": "he",
    "hin_Deva": "hi",
    "hrv_Latn": "hr",
    "hun_Latn": "hu",
    "hye_Armn": "hy",
    "ibo_Latn": "ig",
    "ilo_Latn": "ilo",
    "ind_Latn": "id",
    "isl_Latn": "is",
    "ita_Latn": "it",
    "jav_Latn": "jv",
    "jpn_Jpan": "ja",
    "kat_Geor": "ka",
    "kaz_Cyrl": "kk",
    "khm_Khmr": "km",
    "kor_Hang": "ko",
    "lit_Latn": "lt",
    "ltz_Latn": "lb",
    "lug_Latn": "lg",
    "lvs_Latn": "lv",
    "mal_Mlym": "ml",
    "mar_Deva": "mr",
    "mkd_Cyrl": "mk",
    "mya_Mymr": "my",
    "nld_Latn": "nl",
    "nob_Latn": "no",
    "npi_Deva": "ne",
    "oci_Latn": "oc",
    "ory_Orya": "or",
    "pes_Arab": "fa",
    "plt_Latn": "mg",
    "pol_Latn": "pl",
    "por_Latn": "pt",
    "ron_Latn": "ro",
    "rus_Cyrl": "ru",
    "sin_Sinh": "si",
    "slk_Latn": "sk",
    "slv_Latn": "sl",
    "snd_Arab": "sd",
    "som_Latn": "so",
    "spa_Latn": "es",
    "srp_Cyrl": "sr",
    "sun_Latn": "su",
    "swe_Latn": "sv",
    "swh_Latn": "sw",
    "tam_Taml": "ta",
    "tat_Cyrl": "tt",
    "tgl_Latn": "tl",
    "tur_Latn": "tr",
    "ukr_Cyrl": "uk",
    "urd_Arab": "ur",
    "uzn_Latn": "uz",
    "vie_Latn": "vi",
    "wol_Latn": "wo",
    "xho_Latn": "xh",
    "ydd_Hebr": "yi",
    "yor_Latn": "yo",
    "zho_Hans": "zh",
    "zsm_Latn": "ms",
    "zul_Latn": "zu",
}
