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

TOOLCHAIN_ROOT=/opt/gcc-arm-none-eabi-8-2019-q3-update/bin

AS = $(TOOLCHAIN_ROOT)/arm-none-eabi-as
CCC = $(TOOLCHAIN_ROOT)/arm-none-eabi-g++
CC = $(TOOLCHAIN_ROOT)/arm-none-eabi-gcc
LD = $(TOOLCHAIN_ROOT)/arm-none-eabi-g++
OBJCOPY = $(TOOLCHAIN_ROOT)/arm-none-eabi-objcopy
OBJDUMP = $(TOOLCHAIN_ROOT)/arm-none-eabi-objdump
SIZE = $(TOOLCHAIN_ROOT)/arm-none-eabi-size

# assembler:
ASFLAGS =
# c compiler: target ARM2, use 'mov pc, lr' rather than 'bx lr', skip c++
# exceptions, don't include most of the clib, optimize, include nanopb
CFLAGS = -Wall -Werror -mcpu=arm2 -mno-thumb-interwork -fno-exceptions -ffreestanding -O2 -I../host_mcu_comms -I../third_party/crc32 -I../third_party/nanopb -DPB_FIELD_16BIT -DARCFLASH
CCFLAGS = $(CFLAGS) -std=c++17
# don't include the standard library (which uses 'bx lr' everywhere)
LDFLAGS = -nostdlib
# this was in LDFLAGS, but doesn't appear necessary; did I pull in everything
# needed from arm-trusted-firmware?
# -lgcc

.PHONY: default all build clean

default: dev program

build: all

dev: dev_version build

release: clean release_version all

clean:
	# Work around a bug in proto/Makefile, where it fails if nanopb_pb2.py doesn't exist.
	touch ../third_party/nanopb/generator/proto/nanopb_pb2.py
	make -C ../third_party/nanopb/generator/proto clean
	rm -vf *_boot.bin *.elf *.list *.o *.rom *.pb *.pb.* ../third_party/nanopb/*.o

all: arcflash.rom jump_to_rom.bin ../python_lib/arcflash/bootmenu.bin

dev_version:
	python3 ../python_lib/make_version_id.py dev > version.h

release_version:
	python3 ../python_lib/make_version_id.py  release > version.h

main.o: version.h

%.o: %.s
	$(AS) $(ASFLAGS) -o $@ $<

riscos_font.o: ../third_party/riscos/riscos_font.s
	$(AS) -o $@ $<

%.o: %.cc
	$(CCC) $(CCFLAGS) -c -o $@ $<

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.elf: %.o
	$(LD) $(CFLAGS) $(LDFLAGS) -Wl,--section-start=.text=0 -o $@ $<

%.rom: %.bin
	cp $< $@

# Force protos to build first
cstartup.o: arcflash.pb.h

# nanopb build step
../third_party/nanopb/generator/proto/nanopb_pb2.py: ../third_party/nanopb/generator/proto/nanopb.proto
	cd ../third_party/nanopb/generator/proto; protoc --python_out=. nanopb.proto

arcflash.pb arcflash.pb.c arcflash.pb.h ../python_lib/arcflash/arcflash_pb2.py: arcflash.proto ../third_party/nanopb/generator/proto/nanopb_pb2.py
	protoc -o arcflash.pb --python_out=../python_lib/arcflash $<
	python3 ../third_party/nanopb/generator/nanopb_generator.py arcflash.pb

SHARED_OBJS=cstartup.o \
	arcflash.pb.o \
	descriptor.o \
	printf.o \
	../third_party/arm-trusted-firmware/arm32_aeabi_divmod.o \
	../third_party/arm-trusted-firmware/arm32_aeabi_divmod_a32.o \
	../third_party/arm-trusted-firmware/memcpy.o \
	../third_party/arm-trusted-firmware/memset.o \
	../third_party/crc32/crc32.o \
	../third_party/nanopb/pb_common.o ../third_party/nanopb/pb_encode.o ../third_party/nanopb/pb_decode.o

SWITCHER_OBJS=$(SHARED_OBJS) cmos.o display.o keyboard.o main.o riscos_font.o start.o test.o \
	../host_mcu_comms/host_mcu_comms.o

RPC_BOOT_OBJS=$(SHARED_OBJS) rpc_main.o rpc_start.o

# Arc bootloader that runs from later in ROM, to make room for the Risc PC bootloader.
arc_boot.elf: $(SWITCHER_OBJS)
	@echo "--- BUILD ARCHIMEDES BOOTLOADER ---"
	$(LD) $(CFLAGS) $(LDFLAGS) -Wl,--script=switcher.ld -Wl,-Map,arc_boot.map -o $@ $(SWITCHER_OBJS)
	$(OBJDUMP) -S --disassemble arc_boot.elf > arc_boot.list

# Standalone Arc bootloader that runs from the start of ROM.
arc_boot_standalone.elf: $(SWITCHER_OBJS)
	@echo "--- BUILD STANDALONE ARCHIMEDES BOOTLOADER ---"
	$(LD) $(CFLAGS) $(LDFLAGS) -Wl,--script=switcher-at-zero.ld -Wl,-Map,arc_boot_standalone.map -o $@ $(SWITCHER_OBJS)
	$(OBJDUMP) -S --disassemble arc_boot_standalone.elf > arc_boot_standalone.list

# Risc PC bootloader.
rpc_boot.elf: $(RPC_BOOT_OBJS)
	@echo "--- BUILD RPC BOOTLOADER ---"
	$(LD) $(CFLAGS) $(LDFLAGS) -Wl,--script=rpc_boot.ld -Wl,-Map,rpc_boot.map -o $@ $(RPC_BOOT_OBJS)
	$(OBJDUMP) -S --disassemble rpc_boot.elf > rpc_boot.list

%.bin: %.elf
	$(SIZE) $<
	$(OBJCOPY) -O binary $< $@
	ls -al $@

arcflash.rom: risc_os.bin arc_boot.bin rpc_boot.bin
	python3 merge_binaries.py $@
	# to make addresses correct for Arc: --adjust-vma=0x03800000
	# to make addresses correct for RPC: --adjust-vma=0xfc000000
	$(OBJDUMP) -D -bbinary -marm -Mno-force-thumb -Mreg-names-raw --adjust-vma=0x03800000 $@ > arcflash.list

program: arcflash.rom
	arcflash upload arcflash.rom

../python_lib/arcflash/bootmenu.bin: arcflash.rom
	cp $< $@
