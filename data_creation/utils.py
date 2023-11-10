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


import hashlib

def myhash(s):
    return hashlib.md5(s.encode('utf-8')).digest()[:8]  # TODO: replace newline&tab with ' ', strip ?


def myhash2int(hh):
    assert len(hh) == 8
    return int.from_bytes(hh, byteorder='little', signed=True)


def row_score_to_entry(row, score):
    # pack row, score as an int64-compatable int
    bytes = row.to_bytes(7, byteorder='little', signed=False) + score.to_bytes(1, byteorder='little', signed=False)
    return int.from_bytes(bytes, byteorder='little', signed=True)


def entry_to_row_score(entry):
    # unpack row, score from an int64-compatable int
    bytes = entry.to_bytes(8, byteorder='little', signed=True)
    row = int.from_bytes(bytes[:7], byteorder='little', signed=False)
    score = int.from_bytes(bytes[7:], byteorder='little', signed=False)
    return row, score
