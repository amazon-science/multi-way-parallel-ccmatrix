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


import subprocess as sp

from utils import wmt21_22_lps


def run(cmd):
    print(cmd)
    sp.check_call(cmd, shell=True)


for lp in wmt21_22_lps:
    src, tgt = lp.split('-')
    run(f'python3 extract_and_shuffle.py --langs {src} {tgt}')
    run(f'python3 extract_bitext_subsets.py  {src} {tgt}')
    
    
