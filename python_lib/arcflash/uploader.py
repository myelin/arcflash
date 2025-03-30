# Copyright 2017 Google Inc.
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

# Program a ROM image into an Arcflash board.

# TODO figure out a less CPU intensive way to do this.  We can probably use
# blocking serial comms (that would hang on the ATMEGA32U4) for Arcflash with
# its ATSAMD21.

import re
import time

import arcflash.port

def read_until(ser, match):
    resp = b''
    while True:
        r = ser.read(1024)
        if r:
            print(repr(r))
            resp += r
            if resp.find(match) != -1:
                break
            else:
                time.sleep(0.1)
    return resp

def upload(rom_fn, rom, upload_offset=None, upload_length=None):
    """Upload `upload_length` bytes from image `rom` at offset `upload_offset`."""

    # Flash sectors are 32768 words -- 64KiB per chip, or 128KiB for us.
    SECTOR_SIZE = 32768 * 4

    # Pad out to a full sector if necessary.
    bytes_into_last_sector = len(rom) % SECTOR_SIZE
    if bytes_into_last_sector:
        rom += b"\xff" * (SECTOR_SIZE - bytes_into_last_sector)

    with arcflash.port.Port() as ser:
        print("\n* Port open.  Giving it a kick, and waiting for OK.")
        ser.write(b"\n")
        r = read_until(ser, b"OK")

        print("\n* Requesting chip ID and locking chip")
        ser.write(b"I\n")  # identify chip
        r = read_until(ser, b"OK")
        m = re.search(br"Size = (\d+)", r)
        if not m:
            raise Exception("Chip identification failed")
        chip_size = int(m.group(1))
        print("\n* Chip size = %d bytes" % chip_size)
        usb_block_size = 1024

        if upload_offset is None:
            upload_offset = 0
        if upload_length is None:
            upload_length = len(rom)

        # Check that the image won't overrun the chip.
        if upload_offset + upload_length > chip_size:
            raise Exception(
                f"Can't program {rom_fn} from {upload_offset} to {upload_offset + upload_length} "
                f"as it won't fit in the chip ({chip_size} B capacity)")

        # Upload must begin inside the flash.
        assert 0 <= upload_offset <= chip_size
        # Upload must end inside the flash.
        assert 0 <= upload_length <= chip_size - upload_offset

        print("\n* Start programming process")
        ser.write(f"P {upload_offset} {upload_length}\n".encode())  # program range

        input_buf = b''
        done = 0
        while not done:
            input_buf += read_until(ser, b"\n")
            while input_buf.find(b"\n") != -1:
                p = input_buf.find(b"\n") + 1
                line, input_buf = input_buf[:p], input_buf[p:]
                line = line.strip()
                print("parse",repr(line))
                if line == b"OK":
                    print("All done!")
                    done = 1
                    break
                m = re.search(br"^(\d+)\+(\d+)$", line)
                if not m: continue

                start, size = int(m.group(1)), int(m.group(2))
                print("* [%.1f%%] Sending data from %d-%d" % (start * 100.0 / len(rom), start, start+size))
                blk = rom[start:start+size]
                while len(blk):
                    n = ser.write(blk[:usb_block_size])
                    if n:
                        blk = blk[n:]
                    else:
                        time.sleep(0.01)
