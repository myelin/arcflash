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

# Merge ROM images to create the Arcflash bootloader image

import struct
import sys

output_fn = sys.argv[1]

# Read binaries
risc_os = open("risc_os.bin", "rb").read()
arc_boot = open("arc_boot.bin", "rb").read()
rpc_boot = open("rpc_boot.bin", "rb").read()

# Combine everything.  See README.md for details on memory map.
print(f"Writing combined bootloader image to {output_fn}")
f = open(output_fn, "wb")

# Start with RISC OS
print(f"Writing RISC OS binary at 0")
f.write(risc_os)

arc_offset = len(risc_os) + 8
rpc_offset = arc_offset + len(arc_boot)

print("Arc bootloader at %08x, RPC bootloader at %08x" % (arc_offset, rpc_offset))

# Offset of RPC bootloader
print(f"Writing RPC bootloader offset at {f.tell()}")
f.write(struct.pack("<i", rpc_offset))

# Offset of Arc bootloader
print(f"Writing Arc bootloader offset at {f.tell()}")
f.write(struct.pack("<i", arc_offset))

# Arc bootloader
print(f"Writing Arc bootloader at {f.tell()}")
f.write(arc_boot)

# RPC bootloader
print(f"Writing RPC bootloader at {f.tell()}")
f.write(rpc_boot)

total = f.tell()
print("Arcflash bootloader size %d (%dk, 0x%08x)" % (total, (total+1023)/1024, total))

# And we're done!
f.close()
