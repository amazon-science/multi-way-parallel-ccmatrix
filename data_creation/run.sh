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

# Run on i4i.32xlarge (128vCPU, 1,024 GiB memory, 6Tb gp2 disk, ~11USD/hr, runs in ~26hrs ~= 300USD)
# The final data is ~300GB and is saved as compressed shards with one json line per entry in the directory shards/

time python3 00_download_data.py > log00 #~2.5 hours
time python3 01_create_bin_edges.py > log01 #~1.5 hours
time python3 02_hash_and_bin.py > log02 #~2 hours
time python3 03_build_table.py > log03 #~8 hours
time python3 04_build_hash2sent.py > log04 #~7 hours
time python3 05_make_shards.py > log05 # ~6 hours
