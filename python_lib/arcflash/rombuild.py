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

# Arcflash ROM builder

import importlib.resources
import hashlib
import os
import stat
import struct
import sys

# Force pure-Python protobuf implementation, to avoid version mismatch
# errors.
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
from arcflash import arcflash_pb2
import arcflash.config
import arcflash.uploader

__all__ = ["_1M", "_2M", "_4M", "ROM", "FlashImage"]

_512k = 512*1024
_1M = 1024*1024
_2M = _1M * 2
_4M = _1M * 4

def round_size_up(size):
    for bucket in (_512k, _1M, _2M, _4M):
        if size <= bucket:
            return bucket
    return None

def get_bootloader_binary():
    ref = importlib.resources.files('arcflash') / 'bootmenu.bin'
    with ref.open('rb') as f:
        return f.read()

class ROM:
    def __init__(self, name, files, size=_2M, tag=None, cmos=None):
        self.name, self.files, self.size, self.cmos, self.tag = \
            name, files, size, cmos, tag
        self.ptr = -1  # byte location in flash

    def readable_size(self):
        if self.size < _1M:
            return "%dk" % (self.size/1024)
        return "%dM" % (self.size/_1M)

    def as_proto(self):
        p = arcflash_pb2.FlashBank(
            bank_ptr=self.ptr,
            bank_size=self.size,
            bank_name=self.name,
            )
        if self.tag:
            p.bank_tag = self.tag
        if self.cmos:
            p.cmos_tag = self.cmos
        return p

    def read_files(self):
        data = []
        size = 0
        for fn in self.files:
            fdata = open(fn, "rb").read()
            data.append(fdata)
            size += len(fdata)
        assert size <= self.size, \
            "Read %d bytes for ROM %s, but it's specified to only have %d" % (size, self, self.size)
        data = b"".join(data)
        # calculate checksum
        if 1:
            csum = 0
            for ptr in range(0, len(data)-8, 4):
                v = struct.unpack("<i", data[ptr:ptr+4])
                csum = (csum + v[0]) & 0xffffffff
            print("checksum for %s with len %d: %08x" % (repr(self.files), len(data), csum))
        return (data, size)

    def as_source_proto(self):
        data, size = self.read_files()
        p = arcflash_pb2.SourceRomImage(
            data=data,
            size=size,
            hash_sha1=hashlib.sha1(data).hexdigest(),
            local_path=self.files,
            name=self.name,
            bank_size=self.size,
            )
        if self.tag:
            p.tag = self.tag
        if self.cmos:
            p.cmos_tag = self.cmos
        return p

    def __repr__(self):
        if self.tag:
            if self.name:
                desc = "%s (%s)" % (self.tag, self.name)
            else:
                desc = self.tag
        else:
            desc = self.name
        desc += " [%s]" % self.readable_size()
        return desc

def switch_byte_order(data, byte_order):
    if len(data) % 4:
        # Pad to a multiple of 4 bytes
        if len(data) == 524289 and data[-1] == '\\':
            # Special case for Arthur 1.20 image with extra byte
            print("Dropping the last byte of known Arthur image")
            data = data[:512*1024]
        else:
            n_pad = 4 - (len(data) % 4)
            print("Padding %d-byte image with %d 0xFF bytes" % (len(data), n_pad))
            data += b"\xFF" * n_pad

    if byte_order == "0123":
        return data

    if byte_order == "2301":
        print("Swapping pairs of bytes (Risc PC adapter)")
        output = []
        for idx in range(0, len(data), 4):
            output.append(data[idx+2:idx+3] + data[idx+3:idx+4] + data[idx:idx+1] + data[idx+1:idx+2])
        return b"".join(output)

    if byte_order == "3210":
        print("Reversing bytes in each word (A5000 adapter)")
        output = []
        for idx in range(0, len(data), 4):
            output.append(data[idx+3:idx+4] + data[idx+2:idx+3] + data[idx+1:idx+2] + data[idx:idx+1])
        return b"".join(output)

    raise ValueError("Invalid byte_order value: %s" % byte_order)

def build_image(roms,
                byte_order="0123",
                bootloader_512k=False,
                bootloader_image_override=None,
                skip_bootloader=False):
    # Arcflash v1 has 16MB of flash
    flash_size = _1M * 16
    bootloader_bank_size = 0 if skip_bootloader else _1M

    # Fit ROM images into the space available.  We have 16M, but flash banks
    # must be aligned -- 4M banks must be on a 4M boundary, and 2M banks must
    # be on a 2M boundary.  As such we want to fit in the 4M images first,
    # then 2M, then 1M (with the exception of the bootloader, which is a 1M
    # bank that must be placed at the start of the flash).

    roms_by_size = {}
    for rom in roms:
        roms_by_size.setdefault(rom.size, []).append(rom)
    used_blocks = [(0, bootloader_bank_size)]  # start with a 1M ROM at position zero
    flash_free = flash_size - bootloader_bank_size
    for size, romlist in sorted(roms_by_size.items(), reverse=True):
        for rom in romlist:
            placed = False
            for ptr in range(0, flash_size, size):
                # Check if ptr is in any of the ranges in used_blocks
                block_free = True
                for used_start, used_len in used_blocks:
                    if ptr >= used_start and ptr < used_start + used_len:
                        block_free = False
                        break
                if not block_free: continue

                print("Placing rom %s at flash+%dk" % (repr(rom), ptr/1024))
                used_blocks.append((ptr, rom.size))
                rom.ptr = ptr
                placed = True
                flash_free -= rom.size
                break
            if not placed:
                raise Exception("No room for rom %s.  Need %dk, but only have %dk." % (
                    repr(rom), rom.size/1024, flash_free/1024))
    print("Everything fits; %dk/%dk used, %dk free" % (
        (flash_size-flash_free)/1024, flash_size/1024, flash_free/1024))

    print("\nThe menu will look like:\n")
    romid = 0
    for rom in roms:
        print("%s: %s (%s)" % (chr(romid + ord('A')), rom.name, rom.readable_size()))
        romid += 1
    print()

    descriptor = arcflash_pb2.FlashDescriptor(
        bank=[rom.as_proto() for rom in roms],
        flash_size=flash_size,
        free_space=flash_free,
    )

    # Time to build the flash image!
    # Start by collecting all images aside from the bootloader.
    EXPLAIN_FLASH_BUILD = 0
    flash = b""
    ptr = bootloader_bank_size
    for _, rom in sorted((rom.ptr, rom) for rom in roms):
        if EXPLAIN_FLASH_BUILD: print("Adding %s at %d (currently %d)" % (rom, rom.ptr, ptr))
        assert ptr <= rom.ptr
        if rom.ptr > ptr:
            pad_len = (rom.ptr - ptr)
            if EXPLAIN_FLASH_BUILD: print("- Adding padding of %d bytes first" % pad_len)
            flash += b"\xFF" * pad_len
            ptr += pad_len
        data, size = rom.read_files()
        if size < rom.size:
            data += (b"\xFF" * (rom.size - size))
        data = switch_byte_order(data, byte_order)
        assert len(data) == rom.size, "data is %d bytes long, expected %d" % (len(data), rom.size)
        if EXPLAIN_FLASH_BUILD: print("- Adding %d bytes (ROM %s)" % (len(data), rom))
        flash += data
        ptr += rom.size
    build_flash_size = flash_size - bootloader_bank_size
    if len(flash) < build_flash_size:
        pad_len = build_flash_size - len(flash)
        if EXPLAIN_FLASH_BUILD: print("Adding %d bytes of padding at end" % pad_len)
        flash += b"\xFF" * pad_len
    assert len(flash) == build_flash_size, \
        "Flash should be %d bytes long but it's actually %d" % (build_flash_size, len(flash))

    # TODO add rom image hash to descriptor
    descriptor.hash_sha1 = hashlib.sha1(flash).hexdigest()
    print("Flash images collected; %dk, hash %s" % (len(flash)/1024, descriptor.hash_sha1))

    if skip_bootloader:
        bootloader_bank = ''
    elif bootloader_image_override:
        # Bootloader image overridden -- ignore descriptor etc
        print(f"Overriding usual bootloader; placing {bootloader_image_override} in the bootloader bank.")
        bootloader_binary = open(bootloader_image_override, "rb").read()
        # bootloader_binary = switch_byte_order(bootloader_binary, byte_order)
        bootloader_bank = (
            bootloader_binary +
            (b"\xff" * (bootloader_bank_size - len(bootloader_binary)))
        )
    else:
        # Memory map:
        # 0     - bootloader
        #       - padding (0xff)
        # 896k  - descriptor: length word, followed by data.
        #       - padding (0xff)
        # 1024k - end
        bootloader_size = 1024 * 1024
        descriptor_size = 128 * 1024  # Don't need this much, but it's one flash sector.
        descriptor_pos = bootloader_size - descriptor_size

        # Binaries to pack into this flash bank.
        bootloader_binary = get_bootloader_binary()
        descriptor_binary = descriptor.SerializeToString()

        assert len(bootloader_binary) < descriptor_pos, \
            "Bootloader binary plus descriptor won't fit in %sk - need to change memory map" % (descriptor_pos/1024)
        padding_after_bootloader_size = descriptor_pos - len(bootloader_binary)
        padding_after_descriptor_size = descriptor_size - len(descriptor_binary) - 4

        bootloader_bank = (
            # Start with the binary
            bootloader_binary +
            # Then padding to make binary + padding + descriptor + length == 384k
            (b"\xff" * padding_after_bootloader_size) +
            struct.pack("<i", len(descriptor_binary)) +
            descriptor_binary +
            (b"\xff" * padding_after_descriptor_size)
        )
        print("Bootloader bank contents:")
        blk_ptr = 0
        for blk_desc, blk_size in (
            ("Bootloader", len(bootloader_binary)),
            ("Padding", padding_after_bootloader_size),
            ("Descriptor length", 4),
            ("Descriptor", len(descriptor_binary)),
            ("Padding", padding_after_descriptor_size),
        ):
            print(f"- {blk_ptr:08X}: {blk_desc} ({blk_size} B)")
            blk_ptr += blk_size
        print(f"Total size: {blk_ptr:08X} ({blk_ptr})")
        if bootloader_512k:
            # Hack to allow running the bootloader on an A310 and Arcflash v1 without modifying LK12.
            # Electrically this has LA18 coming in on the nOE pin, but this is OC on Arcflash v1.
            print("Repeating bootloader twice in first 1MB, to accommodate unmodified A310")
            bootloader_bank = bootloader_bank[:512*1024] + bootloader_bank[:512*1024]
        print("Bootloader added.")
    assert(len(bootloader_bank) == bootloader_bank_size)

    # Now put it all together
    flash = switch_byte_order(bootloader_bank, byte_order) + flash
    assert len(flash) <= flash_size, \
        "An error occurred: flash ended up %d bytes long and should be max %d" % (len(flash), flash_size)

    return flash

def FlashImage(roms,
               byte_order="0123",
               bootloader_512k=False,
               bootloader_image_override=None,
               skip_bootloader=False):
    print("Arcflash ROM builder / image flasher\n")

    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    if len(args):
        cmd = args.pop(0)
    else:
        cmd = 'build'

    flash = build_image(roms=roms,
                        byte_order=byte_order,
                        bootloader_512k=bootloader_512k,
                        bootloader_image_override=bootloader_image_override,
                        skip_bootloader=skip_bootloader)

    # And save it!  (Or upload it)
    if cmd == 'save':
        if not len(args):
            raise Exception("Syntax: %s save <filename>" % sys.argv[0])
        fn = args.pop(0)
        print("Saving flash image to %s" % fn)
        with open(fn, "wb") as f:
            f.write(flash)
        return

    if cmd == 'savesrc':
        # Save source proto, for editing with arcflash_image_editor app
        if not len(args):
            raise Exception("Syntax: %s savesrc <filename>" % sys.argv[0])
        fn = args.pop(0)
        ext = '.arcflashsrcimage'
        assert fn.endswith(ext), "Filename must end with %s" % ext
        print("Saving flash source data to %s" % fn)
        src = arcflash_pb2.SourceImageFile(rom=[rom.as_source_proto() for rom in roms])
        with open(fn, "wb") as f:
            f.write(src.SerializeToString())

    if cmd == 'upload':
        print("Uploading to flash")
        arcflash.uploader.upload("Generated image", flash, upload_offset=None, upload_length=None)

def build_rom_from_dir(path):
    print(f"Building ROM image from directory {path}")
    conf = arcflash.config.Config(f"{path}/arcflash.toml")
    roms = []
    for conf_rom in conf.roms():
        # Figure out how big a bank we need for this.
        file_size = os.stat(conf_rom["path"])[stat.ST_SIZE]
        rom_size = round_size_up(file_size)
        if not rom_size:
            raise Exception(f"ROM image {conf_rom['path']} is {file_size} bytes, which won't fit in a 4MB ROM space")

        roms.append(ROM(
            name=conf_rom["name"],
            files=[conf_rom["path"]],
            size=rom_size,
            tag=conf_rom["tag"],
        ))

    return build_image(roms=roms,
                       byte_order=conf.byte_order(),
                       )
