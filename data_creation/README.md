
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

# Data Creation

Steps to create the table:

* [00_download_data.py](00_download_data.py)

    Downloads the CCMatrix dataset (849GB) from https://data.statmt.org/cc-matrix/ and saves it in the directory `raw_data/`

    To run:

    ```commandline
    python3 00_download_data.py
    ```

* [01_create_bin_edges.py](01_create_bin_edges.py)

    This script creates bin edges of margin scores such that each bin has approximately the same number of CCMatrix data examples. The approximate number of bins to be created can be specified in the variable `num_score_bins` of [config.py](config.py).
    
    This script will generate a file `cutoffs.txt`, specifying the margin score cutoff values for each bin, which will be used to sort the data into the relevant bin in the next step. The current [cutoffs.txt](cutoffs.txt) file specifies the cutoffs for sorting the data in ~50 bins.

    To run:

    ```commandline
    python3 01_create_bin_edges.py
    ```

* [02_hash_and_bin.py](02_hash_and_bin.py)

    This script parses the raw CCMatrix bitext data, hashes each sentence and stores it in a directory corresponding to its margin score bin.

    All files created in this step are saved in the directory `binned_data`.

    To run:

    ```commandline
    python3 02_hash_and_bin.py
    ```

* [03_build_table.py](03_build_table.py)

    This script builds the multiway parallel data table by combining data with common sentences across language pairs.

    The hashed bitext pairs from CCMatrix are parsed from the highest to lowest margin score bins from the `binned_data` directory, created in the previous step.

    For a given pair of hashes (hash0, hash1), we first check whether either one is already present in the multiway parallel data table. Then,

    * If both hashes are not in the data, we add them as a new row corresponding to the language pair in the table
    * If one of the hashes is in the data, we assign the second hash to the same row in the table
    * If both the hashes are already in the data, we do nothing

    The data table entries for each language are saved in the `tables_hashed` directory.

    To run:

    ```commandline
    python3 03_build_table.py
    ```

* [04_build_hash2sent.py](04_build_hash2sent.py)

    This script parses the file corresponding to each language in the `tables_hashed` directory, and maps each hashed entry to its corresponding sentence, row and margin score bin. 
    
    This data is then bucketed and saved in *num_buckets* (specified [config.py](config.py)) subdirectories in the `hash2sent` directory.

    To run:

    ```commandline
    python3 04_build_hash2sent.py
    ```


* [05_make_shards.py](05_make_shards.py)

    This script parses the data in the `hash2sent` directory, created in the previous step and saves final table as gzipped shards with one json line per entry.

    Each json line contains a multiway parallel example (consisting of 2 or more translations). Each example stores the languages in which translations exist, along with the respective sentences and margin score bins from which they were added to the table. The following is an example of an entry in the final data with 4 translations-

    ```json
    {
        'en': ['Do not use taxis and other private vehicles because they charge you a lot of money.', 50], 
        'es': ['No use taxis y otros vehículos privados porque le cobran mucho dinero.', 49], 
        'zh': ['不要使用出租车和其他私人车辆，因为他们向你收取很多钱。', 50], 
        'fa': ['از وسایل حمل و نقل عمومی استفاده کنید چرا که تاکسی ها هزینه زیادی از شما دریافت می کنند.', 18]
    }
    ```

    To run:

    ```commandline
    python3 05_make_shards.py
    ```


To execute the complete data creation process, run:

```commandline
bash run.sh
```

On an i4i.32xlarge (128vCPU, 1,024 GiB memory, 6Tb gp2 disk), the entire process ran in ~26hrs.

Breakdown of runtime:

* 00_download_data.py: ~2.5 hours
* 01_create_bin_edges.py: ~1.5 hours
* 02_hash_and_bin.py: ~2 hours
* 03_build_table.py: ~8 hours
* 04_build_hash2sent.py: ~7 hours
* 05_make_shards.py: ~6 hours