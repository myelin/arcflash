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

FROM ubuntu

WORKDIR /scratch

RUN apt-get update && \
    apt-get -y install build-essential bzip2 iverilog make protobuf-compiler python3 python3-protobuf wget

# Install ARM tools with GCC 8, to build boot menu.
RUN wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/8-2019q3/RC1.1/gcc-arm-none-eabi-8-2019-q3-update-linux.tar.bz2 && \
    cd /opt && \
    tar -vjxf /scratch/gcc-arm-none-eabi-8-2019-q3-update-linux.tar.bz2 && \
    rm /scratch/gcc-arm-none-eabi-8-2019-q3-update-linux.tar.bz2

# Install arduino-cli, to build bootloader.
RUN cd /scratch && \
    wget https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz && \
    cd /usr/bin && \
    tar -vzxf /scratch/arduino-cli_latest_Linux_64bit.tar.gz && \
    rm /scratch/arduino-cli_latest_Linux_64bit.tar.gz

# Switch to arcflash user
RUN useradd -ms /bin/bash arcflash
USER arcflash
WORKDIR /home/arcflash

COPY arduino-cli.yaml /scratch

# Install Arduino deps
RUN arduino-cli core update-index && \
    arduino-cli --config-file /scratch/arduino-cli.yaml core install adafruit:samd
