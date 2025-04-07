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

import sys

import setuptools

# pip removes . from the path, so we need to re-add it to import this.
sys.path.insert(0, ".")
import make_version_id

BOSSA = "bossa/src"

setuptools.setup(
    name="arcflash",
    version=make_version_id.get_version(),
    ext_modules=[
        setuptools.Extension(
            name="arcflash._bossa",
            extra_compile_args={
                "win32": ["/std:c++20"],
            }.get(sys.platform, ["-Wno-unqualified-std-cast-call", "-std=c++20"]),
            extra_link_args={
                "win32": ["/DEFAULTLIB:advapi32.lib", "/DEFAULTLIB:setupapi.lib"],
            }.get(sys.platform, []),
            include_dirs=["bossa/src"],
            sources=[
                "bossa-wrapper/_bossa.cc",
            ]
            + [
                f"{BOSSA}/{fn}"
                for fn in [
                    "Samba.cpp",
                    "Flash.cpp",
                    "D5xNvmFlash.cpp",
                    "D2xNvmFlash.cpp",
                    "EfcFlash.cpp",
                    "EefcFlash.cpp",
                    "Applet.cpp",
                    "WordCopyApplet.cpp",
                    "WordCopyArm.cpp",
                    "Flasher.cpp",
                    "Device.cpp",
                ]
                + {
                    "darwin": [
                        "PosixSerialPort.cpp",
                        "OSXPortFactory.cpp",
                    ],
                    "linux": [
                        "PosixSerialPort.cpp",
                        "LinuxPortFactory.cpp",
                    ],
                    "win32": [
                        "WinSerialPort.cpp",
                        "WinPortFactory.cpp",
                    ],
                }.get(sys.platform, [])
            ],
        ),
    ]
)
