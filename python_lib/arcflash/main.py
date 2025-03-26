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

import argparse
import os
import sys
import re

from . import program_cpld
from . import uploader

def main():
    parser = argparse.ArgumentParser(description='Arcflash command line tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'arcflash upload'
    upload_parser = subparsers.add_parser('upload', help='Upload a flash image file to a connected Arcflash board')
    upload_parser.add_argument('filename', help='Path to the flash image file to upload')
    # TODO ' (optionally path@offset+length)'

    # 'arcflash program-cpld'
    program_cpld_parser = subparsers.add_parser('program-cpld', help='Program CPLD on a connected Arcflash board')
    program_cpld_parser.add_argument('filename', help='Path to the SVF file to upload')

    args = parser.parse_args()

    if args.command == 'upload':
        # Upload something into flash.

        # Read image to upload.
        filename, offset, length = args.filename, None, None
        # TODO implement "program range" command, then enable below code:
        # m = re.search(r"(.*?)(?:@(\d+)(?:(\+(\d+))))", args.filename)
        # filename, offset, length = m.groups()
        # offset = int(offset) if offset else None
        # length = int(length) if length else None
        if not os.path.exists(filename):
            print(f"Flash image file {filename} not found")
            return 1

        with open(filename, 'rb') as f:
            image = f.read()

        uploader.upload(filename, image, offset, length)
        return 0

    if args.command == 'program-cpld':
        # Program CPLD.
        return program_cpld.program(args.filename)

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())
