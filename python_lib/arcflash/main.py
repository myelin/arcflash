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

import arcflash._bossa
import arcflash.program_cpld
import arcflash.uploader

def main():
    parser = argparse.ArgumentParser(description='Arcflash command line tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'arcflash program-cpld'
    program_cpld_parser = subparsers.add_parser('program-cpld', help='Program CPLD on a connected Arcflash board')
    program_cpld_parser.add_argument('filename', help='Path to the SVF file to upload')

    # 'arcflash program-mcu'
    program_mcu_parser = subparsers.add_parser('program-mcu', help='Program microcontroller firmware on a connected Arcflash board')
    program_mcu_parser.add_argument('filename', help='Path to the .bin file to upload')

    # 'arcflash upload'
    upload_parser = subparsers.add_parser('upload', help='Upload a flash image file to a connected Arcflash board')
    upload_parser.add_argument('filename', help='Path to the flash image file to upload')
    # TODO ' (optionally path@offset+length)'

    args = parser.parse_args()

    if args.command == 'program-cpld':
        # Program CPLD.
        return arcflash.program_cpld.program(args.filename)

    if args.command == 'program-mcu':
        # Program microcontroller firmware.
        port = arcflash.port.guess_port()
        if not port:
            print("Could not guess serial port")
            return 1
        r = arcflash._bossa.program(port, args.filename)
        if r:
            return 1

        print("\n"
            "Done!  If you get a popup about ARCBOOT not being ejected properly, ignore it;\n"
            "it's a side effect of the UF2 bootloader resetting after the download.")
        return 0

    if args.command == 'upload':
        # Upload something into flash.

        # Read image to upload.
        m = re.fullmatch(r"(.*?)(?:\@(\d+)(?:\+(\d+))?)?", args.filename)
        print(m.groups())
        filename, offset, length = m.groups()
        offset = int(offset) if offset else None
        length = int(length) if length else None
        if not os.path.exists(filename):
            print(f"Flash image file {filename} not found")
            return 1

        with open(filename, 'rb') as f:
            image = f.read()

        arcflash.uploader.upload(filename, image, offset, length)
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())
