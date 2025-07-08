#!/usr/bin/env python3

import os
import argparse

from migen import *

from litex.soc.integration.soc import *
from litex.soc.cores.i2s import *
from litex.soc.cores.gpio import *
from litex.soc.cores.pwm import PWM
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster
from litex_boards.platforms import digilent_arty as arty_platform
from litex.soc.cores.gpio import GPIOOut, GPIOIn

from liteeth.phy.mii import LiteEthPHYMII

# Helpers ------------------------------------------------------------------------------------------

def platform_request_all(platform, name):
    from litex.build.generic_platform import ConstraintError
    r = []
    while True:
        try:
            r += [platform.request(name, len(r))]
        except ConstraintError:
            break
    if r == []:
        raise ValueError
    return r

# SoCZephyr -----------------------------------------------------------------------------------------

def SoCZephyr(soc_cls, **kwargs):
    class _SoCZephyr(soc_cls):
        csr_map = {**soc_cls.csr_map, **{
            "ctrl":       0, # addr: 0xe0000000
            "uart":       3, # addr: 0xe0001800
            "spi":        4, # addr: 0xe0002000
            "timer0":     5, # addr: 0xe0002800
            "sdram":      6, # addr: 0xe0003000
            "uartphy":    7, # addr: 0xe0004000
            "mmcm":       9, # addr: 0xe0004800
            "i2c0":       10, # addr: 0xe0005000
            "rgb_led_r0": 14, # addr: 0xe0007000
            "ethphy":     16, # addr: 0xe0008000
            "ethmac":     19, # addr: 0xe0009800
            "i2s_rx":     21, # addr: 0xe000a800
            "i2s_tx":     22, # addr: 0xe000b000
            "ddrphy":     23, # addr: 0xe000b800
            "spiflash":   24, # addr: 0xe000c000
            "watchdog0":  26, # addr: 0xe000d000
            "litei2c":    27, # addr: 0xe000d800
        }}

        interrupt_map = {**soc_cls.interrupt_map, **{
            "timer0":     1,
            "uart":       2,
            "ethmac":     3,
            "i2s_rx":     6,
            "i2s_tx":     7,
            "watchdog0":  8,
            "spiflash":   9,
            "litei2c":   10,
        }}

        mem_map_zephyr = {
            "rom":          0x00000000,
            "sram":         0x01000000,
            "main_ram":     0x40000000,
            "spiflash":     0x60000000,
            "ethmac":       0xb0000000,
            "i2s_rx":       0xb1000000,
            "i2s_tx":       0xb2000000,
            "csr":          0xe0000000,
        }

        def __init__(self, cpu_variant="standard", **kwargs):
            soc_cls.__init__(self,
                cpu_type="vexriscv",
                cpu_variant=cpu_variant,
                csr_data_width=32,
                max_sdram_size=0x10000000, # Limit mapped SDRAM to 256MB for now
                timer_uptime=True,
                **kwargs)
            soc_cls.mem_map.update(self.mem_map_zephyr)

        def add_rgb_led(self):
            rgb_led_pads = self.platform.request("rgb_led", 0)
            setattr(self.submodules, "rgb_led_r0", PWM(getattr(rgb_led_pads, 'r')))

        def add_i2c(self):
            self.submodules.i2c0 = I2CMaster(self.platform.request("i2c", 0))

        def add_i2s(self):
            self.platform.add_extension(arty_platform._i2s_pmod_io)
            i2s_mem_size = 0x40000
            # i2s rx
            self.submodules.i2s_rx = S7I2S(
                pads=self.platform.request("i2s_rx"),
                sample_width=24,
                frame_format=I2S_FORMAT.I2S_STANDARD,
                concatenate_channels=False,
                toolchain=kwargs["toolchain"]
            )
            self.add_memory_region("i2s_rx", self.mem_map_zephyr["i2s_rx"], i2s_mem_size, type="io")
            self.add_wb_slave(self.mem_regions["i2s_rx"].origin, self.i2s_rx.bus, i2s_mem_size)
            # i2s tx
            self.submodules.i2s_tx = S7I2S(
                pads=self.platform.request("i2s_tx"),
                sample_width=24,
                frame_format=I2S_FORMAT.I2S_STANDARD,
                master=True,
                concatenate_channels=False,
                toolchain=kwargs["toolchain"]
            )
            self.add_memory_region("i2s_tx", self.mem_map_zephyr["i2s_tx"], i2s_mem_size, type="io")
            self.add_wb_slave(self.mem_regions["i2s_tx"].origin, self.i2s_tx.bus, i2s_mem_size)

            self.comb += self.platform.request("i2s_rx_mclk").eq(self.cd_mmcm_clkout["i2s_rx"].clk)
            self.comb += self.platform.request("i2s_tx_mclk").eq(self.cd_mmcm_clkout["i2s_tx"].clk)

        def add_mmcm(self, freqs={}):
            self.cd_mmcm_clkout = {}
            self.submodules.mmcm = S7MMCM(speedgrade=-1)
            self.mmcm.register_clkin(self.crg.cd_sys.clk, self.clk_freq)

            self.add_constant("clkout_def_freq", int(self.clk_freq))
            self.add_constant("clkout_def_phase", int(0))
            self.add_constant("clkout_def_duty_num", int(50))
            self.add_constant("clkout_def_duty_den", int(100))
            self.add_constant("mmcm_lock_timeout", int(10))
            self.add_constant("mmcm_drdy_timeout", int(10))

            for n, key in enumerate(freqs):
                self.cd_mmcm_clkout.update({key : ClockDomain(name="cd_mmcm_clkout{}".format(n))})
                self.mmcm.create_clkout(self.cd_mmcm_clkout[key], freqs[key])

            for n in range(len(freqs), 7):
                key = "clk_{}".format(n)
                self.cd_mmcm_clkout.update({key : ClockDomain(name="cd_mmcm_clkout{}".format(n))})
                self.mmcm.create_clkout(self.cd_mmcm_clkout[key], self.clk_freq)

            self.mmcm.expose_drp()
            self.comb += self.mmcm.reset.eq(self.mmcm.drp_reset.re)

    return _SoCZephyr(**kwargs)
