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

# Utils

This directory contains information and statistics about the CCMatrix dataset which are used in the multiway parallel data creation and analysis.

* [ccmatrix_langpairs.py](ccmatrix_utils/ccmatrix_langpairs.py)

    Contains lists of all language pairs (`CCMATRIX_LANG_PAIRS`) and languages (`CCMATRIX_LANGS`) in CCMatrix, sorted by the amount of data in the dataset.

* [ccmatrix_counts/](ccmatrix_utils/ccmatrix_counts/)

    This directory contains two pickled dictionaries, `lang_counts.pickle` and `langpair_counts.pickle`, which store the number of examples for each language and language pair in the CCMatrix dataset.