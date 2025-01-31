#!/bin/bash

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euxo pipefail

HERE=$(dirname $0)
rm -rf env2 env3

unset PYTHONHOME
ORIG_PATH="$PATH"

python2 -m virtualenv env2
export VIRTUAL_ENV=$HERE/env2
export PATH=$VIRTUAL_ENV/bin:$ORIG_PATH
pip install -e .

python3 -m venv env3
export VIRTUAL_ENV=$HERE/env3
export PATH=$VIRTUAL_ENV/bin:$ORIG_PATH
pip install -e .
