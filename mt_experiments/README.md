  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
  
  Licensed under the Apache License, Version 2.0 (the "License").
  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at
  
      http://www.apache.org/licenses/LICENSE-2.0
  
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

# MT Experiments

This directory contains scripts to extract bitext / bitext subsets for MT experiments. 



To create bitext from the table, keeping track of how multi-way parallel each line was (output is written to directory specified in ```utils.py```, defaults to ```./data```):
```commandline
python3 extract_and_shuffle.py --langs en fr 
```

To create subsets of data for MT experiments (output is written to directory specified in ```utils.py```, defaults to ```./data2```):
```commandline
python3 extract_bitext_subsets.py en fr 
```

To extract and process bitext for all WMT{21,22} language pairs:
```commandline
python3 make_wmt_subsets.py
```
