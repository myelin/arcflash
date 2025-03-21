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

# Shared env
ENV=$HOME/pypi-env
# ENV=$(dirname $0)/env

if [ ! -d "$ENV" ]; then
    python3 -m venv $ENV
fi

# activate our virtualenv
export VIRTUAL_ENV=$ENV
export PATH=$ENV/bin:$PATH
unset PYTHONHOME

# install prereqs
pip install twine wheel keyring

# build the package
rm -rf build dist
python setup.py sdist bdist_wheel --universal

# push to pypi
python -m twine upload -u myelin dist/*
