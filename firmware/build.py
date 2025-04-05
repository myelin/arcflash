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
std_args = "--verbose --fqbn myelin:samd:arcflash --config-file arduino-cli.yaml"

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
