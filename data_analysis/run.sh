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

# The reported runtimes are for an i4i.32xlarge instance (128vCPU, 1,024 GiB memory, 6Tb gp2 disk)

time python3 compute_analysis_stats.py > stats.out #~10 min
time python3 plot_stats.py > stats_plot.out # few seconds
time python3 compute_marginscore_stats.py > ms.out # ~5 min when lang is 'zh', ~15 min when lang is 'en'
time python3 plot_marginscore_stats.py > ms_plot.out # ~15 min when plotting es and fr
time python3 sample_sentences_per_bin.py > sample.out #  ~15-20 min for sampling 'en'
