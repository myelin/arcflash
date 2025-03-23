#!/usr/bin/env python3

# Copyright 2025 Google Inc.
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


import cocotb
from cocotb.handle import Force, Release
from cocotb.clock import Clock
from cocotb.triggers import Timer, FallingEdge, RisingEdge


def tick():
    return Timer(1, units="ns")


async def wait_one_clock_cycle(dut):
    dut.cpld_clock_from_mcu.value = 0
    await tick()
    dut.cpld_clock_from_mcu.value = 1
    await tick()


async def drop_rom_nCS_and_wait_to_settle(dut):
    # Set rom_nCS high for a few clock cycles.
    dut.rom_nCS.value = 1
    for i in range(1):
        await wait_one_clock_cycle(dut)
    # Drop rom_nCS and wait for enough cpld_clock_from_mcu cycles.
    dut.rom_nCS.value = 0
    for i in range(9):
        await wait_one_clock_cycle(dut)


def fmt_byte_array(data):
    return " ".join("%02X" % c for c in data)


async def spi_send_byte(dut, b):
    r = 0
    for _ in range(8):
        dut.cpld_MOSI.value = (b & 0x80) >> 7
        await tick()
        dut.cpld_SCK.value = 1
        await tick()
        dut.cpld_SCK.value = 0
        # dut._log.info(
        #     "spi; cpld_MISO=%s enable_bitbang_serial=%s cpld_SS+%s cpld_MISO_TXD=%s cpld_MISO_int=%s",
        #     dut.cpld_MISO.value,
        #     dut.enable_bitbang_serial,
        #     dut.cpld_SS.value,
        #     dut.cpld_MISO_TXD.value,
        #     dut.cpld_MISO_int.value,
        # )
        r = (r << 1) | dut.cpld_MISO.value
        b = (b << 1) & 0xFF
    return r


async def spi_send(dut, spi_bytes):
    await tick()
    dut.cpld_SS.value = 0
    dut.cpld_SCK.value = 0
    await tick()
    ret = []
    expected_bits = 0
    for b in spi_bytes:
        ret.append(await spi_send_byte(dut, b))
        expected_bits = (expected_bits + 8) % 64
        assert (
            dut.spi_bit_count == expected_bits
        ), "spi_bit_count is %d but expected %d" % (dut.spi_bit_count, expected_bits)
    dut.cpld_SS.value = 1
    await tick()

    dut._log.info(
        "spi transaction: sent %s received %s",
        fmt_byte_array(spi_bytes),
        fmt_byte_array(ret),
    )
    return ret


async def spi_flash_write(dut, addr, data):
    await spi_send(
        dut,
        [
            # 0, RnW, 22 address bits, 32 data bits, 8 zeroes.
            (addr & 0x3F0000) >> 16,
            (addr & 0xFF00) >> 8,
            addr & 0xFF,
            (data & 0xFF000000) >> 24,
            (data & 0xFF0000) >> 16,
            (data & 0xFF00) >> 8,
            data & 0xFF,
            0,
        ],
    )


async def spi_flash_read(dut, addr):
    resp = await spi_send(
        dut,
        [
            # 0, RnW, 22 address bits, 40 zeroes.
            ((addr & 0x3F0000) >> 16) | 0x40,
            (addr & 0xFF00) >> 8,
            addr & 0xFF,
            0,
            0,
            0,
            0,
            0,
        ],
    )
    return (resp[-4] << 24) | (resp[-3] << 16) | (resp[-2] << 8) | resp[-1]


def init(dut):
    dut.rom_5V.value = 1
    dut.rom_nCS.value = 0
    dut.flash0_DQ = Release()
    dut.flash1_DQ = Release()
    dut.rom_nOE.value = 0
    dut.cpld_MISO_int.value = 1
    dut.cpld_MISO_TXD.value = 0
    dut.spi_A = 0
    dut.spi_D = 0
    dut.spi_bit_count.value = 0


@cocotb.test()
async def test_disable_arm_access(dut):
    """Test that initial 0 to SPI disables ARM access."""

    init(dut)

    spi_resp = await spi_send(dut, [0x7F, 0xFF, 0xFF, 0xFF])
    dut._log.info("allowing_arm_access: %s", dut.allowing_arm_access.value)
    dut._log.info(
        "flash nCE %s nOE %s nWE %s",
        dut.flash_nCE.value,
        dut.flash_nOE.value,
        dut.flash_nWE.value,
    )
    assert dut.allowing_arm_access.value == 0
    assert dut.flash_nCE.value == 1
    assert dut.flash_nOE.value == 1
    assert dut.flash_nWE.value == 1


@cocotb.test()
async def test_enable_arm_access(dut):
    """Test that initial 1 to SPI enables ARM access."""

    init(dut)

    spi_resp = await spi_send(dut, [0xFF, 0xFF, 0xFF, 0xFF])
    dut._log.info("allowing_arm_access: %s", dut.allowing_arm_access.value)
    dut._log.info(
        "flash nCE %s nOE %s nWE %s",
        dut.flash_nCE.value,
        dut.flash_nOE.value,
        dut.flash_nWE.value,
    )
    assert dut.allowing_arm_access.value == 1
    assert dut.flash_nCE.value == 0
    assert dut.flash_nOE.value == 0
    assert dut.flash_nWE.value == 1


@cocotb.test()
async def test_mcu_read_from_flash(dut):
    """Test that an SPI read command reads a word from flash."""

    init(dut)

    # Read command: 0, 0, 22 address bits, 40 zeroes.
    # Data is in the last four bytes of the SPI response.
    test_word = 0x12345678
    dut.flash1_DQ.value = Force((test_word >> 16) & 0xFFFF)
    dut.flash0_DQ.value = Force(test_word & 0xFFFF)
    read_resp = await spi_flash_read(dut, 0x3BCDEF)
    dut._log.info(
        "Word read: %08X; flash_DQ %X %X",
        read_resp,
        dut.flash1_DQ.value,
        dut.flash0_DQ.value,
    )
    assert (
        dut.allowing_arm_access.value == 0
    ), "Flash read should leave ARM access disabled"
    assert (
        read_resp == test_word
    ), "Flash read returned incorrect data: %08X instead of %08X" % (
        read_resp,
        test_word,
    )


async def catch_flash_write(dut):
    await FallingEdge(dut.flash_nWE)
    dut._log.info(
        "spotted a flash write: addr %08X data %04X %04X",
        dut.flash_A.value,
        dut.flash1_DQ.value,
        dut.flash0_DQ.value,
    )
    return (dut.flash_A.value, (dut.flash1_DQ.value << 16) | dut.flash0_DQ.value)


@cocotb.test()
async def test_mcu_write_to_flash(dut):
    """Test that an SPI write command writes a word to flash."""

    init(dut)

    write_catcher = await cocotb.start(catch_flash_write(dut))

    # Write command: 0, 0, 22 address bits, 32 data bits, 8 zeroes.
    test_addr = 0x3ABCDE
    test_word = 0x12345678
    await spi_flash_write(dut, test_addr, test_word)
    assert (
        dut.allowing_arm_access.value == 0
    ), "Flash write should leave ARM access disabled"

    await write_catcher.join()
    A, D = write_catcher.result()
    assert A == test_addr, "Flash write has wrong address %X (expected %X)" % (
        A,
        test_addr,
    )
    assert D == test_word, "Flash write has wrong data %X (expected %X)" % (
        D,
        test_word,
    )


@cocotb.test()
async def test_bitbang_serial_writes_from_arm(dut):
    """Test that the ARM can write to the serial port when enabled."""

    init(dut)

    # In between ROM accesses, rom_nCS is high.
    dut.rom_nCS.value = 1

    # First enable ARM access so we can access the serial port memory region
    await spi_send(dut, [0xFF, 0xFF, 0xFF, 0xFF])
    assert dut.allowing_arm_access.value == 1, "Failed to enable ARM access"

    # Make sure the serial port is enabled.
    dut.cpld_SS.value = 1  # disable SPI
    await spi_send(dut, [0x80, 0x00, 0x00, 0x00])
    assert dut.disable_serial_port.value == 0, "Failed to enable serial port"
    assert dut.allowing_arm_access.value == 1, "ARM access should still be enabled"

    # Test setting TXD to 1
    dut.rom_A.value = 0xFFFFD  # A[1:0] = 01
    await drop_rom_nCS_and_wait_to_settle(dut)
    assert dut.cpld_MISO_TXD.value == 1, "Failed to set TXD to 1"
    assert dut.cpld_MISO.value == 1, "Failed to set cpld_MISO to 1"

    # Test setting TXD to 0
    dut.rom_A.value = 0xFFFFC  # A[1:0] = 00
    await drop_rom_nCS_and_wait_to_settle(dut)
    assert dut.cpld_MISO_TXD.value == 0, "Failed to set TXD to 0"
    assert dut.cpld_MISO.value == 0, "Failed to set cpld_MISO to 0"

    # Verify that when cpld_SS is low, cpld_MISO follows cpld_MISO_int instead.
    dut.cpld_SS.value = 0
    dut.cpld_MISO_int.value = 0
    await tick()
    assert dut.cpld_MISO.value == 0, "cpld_SS == 0 should disable the serial port"
    dut.cpld_MISO_int.value = 1
    await tick()
    assert dut.cpld_MISO.value == 1, "cpld_SS == 0 should disable the serial port"

    dut.cpld_SS.value = 1
    await tick()
    assert dut.cpld_MISO.value == 0, "cpld_SS == 1 should re-enable the serial port"

    # Test that disabling the serial port prevents writes to TXD.
    await spi_send(dut, [0xC0, 0x00, 0x00, 0x00])  # Set disable_serial_port bit

    # Try to change TXD (should have no effect now)
    assert dut.cpld_MISO_TXD.value == 0, "cpld_MISO_TXD should still be 0"
    dut.rom_A.value = 0xFFFFD  # Try to set TXD to 1
    await drop_rom_nCS_and_wait_to_settle(dut)
    assert (
        dut.cpld_MISO_TXD.value == 0
    ), "TXD value changed when serial port was disabled"


@cocotb.test()
async def test_bitbang_serial_writes_from_mcu(dut):
    """Test that the MCU can write to the serial port when enabled."""

    init(dut)

    # Disable the serial port to start with.
    await spi_send(dut, [0xC0, 0x00, 0x00, 0x00])
    assert dut.disable_serial_port.value == 1, "Failed to disable serial port"

    # Verify that reads to 0xFFFFF return flash_DQ.
    for val in (0, 1):
        dut.flash1_DQ.value = 0
        dut.flash0_DQ.value = val
        dut.rom_A.value = 0xFFFFF
        await tick()
        assert dut.rom_D.value == val, (
            "ROM %d bit didn't pass through with disabled serial port" % val
        )

    # Enable the serial port.
    await spi_send(dut, [0x80, 0x00, 0x00, 0x00])
    assert dut.disable_serial_port.value == 0, "Failed to enable serial port"

    # Verify that reads to 0xFFFFF return cpld_MOSI.
    for val in (0, 1):
        dut.cpld_MOSI.value = val
        dut.rom_A.value = 0xFFFFF
        await drop_rom_nCS_and_wait_to_settle(dut)
        assert dut.rom_D.value == val, (
            "ROM %d bit didn't pass through with enabled serial port" % val
        )
