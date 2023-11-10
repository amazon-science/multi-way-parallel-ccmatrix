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


import pathlib

num_buckets = 100
local_table_shards_dir = "../data_creation/shards"
# aws s3 cp --recursive s3://multiway-parallel-table/multiway_table_shards/ /home/ubuntu/data_creation/shards/  # aws-translate-dev@amazon.com account

bitex_data_dir = './data'
pathlib.Path(bitex_data_dir).mkdir(parents=True, exist_ok=True)

subset_data_dir = './data2'
pathlib.Path(subset_data_dir).mkdir(parents=True, exist_ok=True)

wmt21_22_lps = ['en-de', 'en-cs', 'en-ru', 'en-zh', 'bn-hi', 'en-is', 'fr-de',
                'en-ja', 'en-ha', 'uk-en', 'uk-cs', 'en-hr']  # not in ccMatrix: 'liv-en', 'sah-ru', almost no data: 'xh-zu'

width_ranges = ((2, 3), (3, 5), (5, 8), (8, 100))
