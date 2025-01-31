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

import random

from arcflash import uploader

def main():
    print("Programming 16MB of random data into Arcflash to see if we can crash the serial port")

    SIZE = 16*1024*1024
    # Python 3.9 lets us do this, but Ubuntu doesn't have 3.9 yet: rom = random.randbytes(SIZE)
    rom = random.Random().getrandbits(SIZE * 8).to_bytes(SIZE, 'little')
    uploader.upload(rom)

if __name__ == '__main__':
    main()
