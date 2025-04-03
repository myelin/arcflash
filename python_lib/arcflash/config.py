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

import hashlib
import os

import tomlkit

CONFIG_PATH = "arcflash.toml"


class Config:
    def __init__(self, fn, allow_empty=False):
        self.fn = fn

        if os.path.exists(fn):
            print(f"Reading config from {fn}.")
            with open(fn, "r") as f:
                self.conf = tomlkit.parse(f.read())
        elif allow_empty:
            print(f"Creating new config at {fn}.")
            self.conf = {}
        else:
            raise Exception(f"Config {fn} not found")

    def save(self):
        tempfn = f".{self.fn}"
        with open(tempfn, "w") as f:
            f.write(tomlkit.dumps(self.conf))
        os.rename(tempfn, self.fn)
        print(f"Wrote config to {self.fn}")

    def find_rom(self, tag=None, path=None):
        assert tag or path, "Must supply either tag or path"
        for image in self.conf.get("roms", []):
            if image["tag"] == tag:
                return image
            if image["path"] == path:
                return image

    def add_rom(self, rom):
        self.conf.setdefault("roms", []).append(rom)

    # Accessors

    def byte_order(self):
        return self.conf.get("byte_order", "0123")

    def roms(self):
        return self.conf["roms"]


def update_config(roms):
    conf = Config(CONFIG_PATH)

    for rom_fn in roms:
        rom = conf.find_rom(path=rom_fn)
        if rom:
            print(f"Already have ROM image {rom}")
            continue
        print(f"Adding ROM image {rom_fn}")
        data = open(rom_fn, "rb").read()
        new_rom = {
            "tag": rom_fn,
            "name": rom_fn,
            "path": rom_fn,
            "hash_sha1": hashlib.sha1(data).hexdigest(),
        }
        conf.add_rom(new_rom)

    conf.save()

    print(
        "You will likely want to edit the configuration file to reorder any new ROMs and give them nicer names."
    )
