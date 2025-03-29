# Copyright 2025 Google LLC
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

"""Basic tests to make sure everything is importable."""

import os

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import arcflash._bossa
import arcflash.port
import arcflash.program_cpld
import arcflash.arcflash_pb2


def test_basic():
    # Make sure the _bossa extension built OK, and
    # _bossa.cc's entry point is accessible.
    assert arcflash._bossa.program is not None
    print("_bossa.program exists")

    # Make sure arcflash.port.guess_port() is runnable.
    port = arcflash.port.guess_port()
    print(f"Guessed port: {port}")

    # Make sure protobuf code doesn't crash.
    p = arcflash.arcflash_pb2.FlashBank(
        bank_ptr=123,
        bank_size=456,
        bank_name="hello",
    )
    print(f"Instantiated a proto: {p}")
