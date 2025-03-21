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

import os
import shutil
import subprocess
import sys

import serial.tools.list_ports

assert sys.version_info[0] >= 3, "Python 3+ required"

def cmd(s):
    print(s)
    return subprocess.check_call(s, shell=True)

here = os.getcwd()
build_path = os.environ.get('ARCFLASH_BUILD')
if not build_path:
    build_path = os.path.join(
        here,
        "build_output_%s" % sys.platform,  # just in case things differ between platforms
    )

# By default, we don't cache anything; set ARCFLASH_CACHE=1 to build quicker
clean_first = os.environ.get("ARCFLASH_CACHE") != "1"

# Allow overriding arduino-cli with a local version
arduino_cli = os.environ.get("ARDUINO_CLI", "arduino-cli")

# std_args = "--verbose --fqbn arduino:samd:adafruit_circuitplayground_m0"
std_args = "--verbose --fqbn myelin:samd:arcflash --config-dir ."

# Figure out where the Arcflash is plugged in
upload_port = arcflash_port = circuitplay_port = None
for port in serial.tools.list_ports.comports():
    print(port.device,
        port.product,
        port.hwid,
        port.vid,
        port.pid,
        port.manufacturer,  # "Adafruit"
    )
    if port.vid == 0x1209 and port.pid == 0xFE07:
        print("Found an Arcflash at %s" % port.device)
        arcflash_port = port.device
    elif port.vid == 0x239A and port.pid in (0x0018, 0x8018):
        print("Found a Circuit Playground Express at %s" % port.device)
        circuitplay_port = port.device

if "ARCFLASH_PORT" in os.environ:
    upload_port = os.environ["ARCFLASH_PORT"]
    print("Using %s from ARCFLASH_PORT environment variable" % upload_port)
elif arcflash_port:
    upload_port = arcflash_port
elif circuitplay_port:
    raise Exception("No Arcflash found, only a Circuit Playground Express.  Is this an Arcflash running the old bootloader?  Update the bootloader then try programming firmware again.")

if not upload_port:
    raise Exception("Could not find a connected Arcflash")

print("Using %s as the upload port" % upload_port)

# Make sure we have the libxsvf submodule.
xsvf_path = "../third_party/libxsvf"
if not os.path.exists(f"{xsvf_path}/libxsvf.h"):
    raise Exception("libxsvf files missing; did you run `git submodule update --init`?")

# Copy libraries into here, so arduino-cli will build them.
for src_dir, dest_dir in [
    ("../host_mcu_comms", "lib/host_mcu_comms"),
    ("../third_party/crc32", "lib/crc32"),
    (xsvf_path, "lib/libxsvf"),
]:
    if clean_first and os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    for f in os.listdir(src_dir):
        if os.path.splitext(f)[1] not in (".c", ".cc", ".cpp", ".h"): continue
        if f.endswith("_test.cc"): continue
        if f in ("xsvftool-ft232h.c", "xsvftool-gpio.c"): continue
        src = os.path.join(src_dir, f)
        dest = os.path.join(dest_dir, f)

        content = open(src).read()
        if not os.path.exists(dest) or open(dest).read() != content:
            open(dest, "w").write(content)
            print("  %s -> %s" % (src, dest))

# Build it
cmd("%s compile %s %s --libraries lib --build-path %s" % (
    arduino_cli,
    "--clean" if clean_first else "",
    std_args,
    build_path,
))

cmd(f"cp -v {build_path}/firmware.ino.bin ./")

if upload_port == 'none':
    print("Skipping uploading as upload_port == none")
else:
    # And upload to the Arcflash board
    cmd("%s upload %s --port %s --input-file firmware.ino.bin" % (
        arduino_cli,
        std_args,
        upload_port,
    ))

    print("\n"
          "Done!  If you get a popup about ARCBOOT not being ejected properly, ignore it;\n"
          "it's a side effect of the UF2 bootloader resetting after the download.")
