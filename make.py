#!/usr/bin/env python3

import argparse
import os

from litex.build.sim.config import SimConfig
from litex.build.xilinx.vivado import vivado_build_args, vivado_build_argdict
from litex.build.lattice.oxide import oxide_argdict, oxide_args
from litex.soc.integration.builder import *

from soc_zephyr import SoCZephyr

# Board definition ---------------------------------------------------------------------------------

class Board:
    soc_kwargs = {
        "integrated_rom_size"  : 0xfa00,
    }
    builder_kwargs = {
    }
    def __init__(self, soc_cls, soc_capabilities={}):
        self.soc_cls = soc_cls
        self.soc_capabilities = soc_capabilities
        self.mmcm_freq = {}

    def load(self, soc, filename):
        prog = soc.platform.create_programmer()
        prog.load_bitstream(filename)

    def flash(self):
        raise NotImplementedError

#---------------------------------------------------------------------------------------------------
# Xilinx Boards
#---------------------------------------------------------------------------------------------------

# Arty support -------------------------------------------------------------------------------------

class Arty(Board):
    def __init__(self):
        from litex_boards.targets import digilent_arty
        Board.__init__(self, digilent_arty.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "spiflash",
            # GPIOs
            "rgb_led",
            # Buses
            "spi",
            "i2c",
            "i2s",
            # 7-Series specific
            "mmcm",
        })
        self.mmcm_freq = {
            "i2s_rx" :  11.289e6,
            "i2s_tx" :  22.579e6,
        }

#---------------------------------------------------------------------------------------------------
# Lattice Boards
#---------------------------------------------------------------------------------------------------

# Antmicro SDI/MIPI Video Converter support --------------------------------------------------------

class SDI_MIPI_Bridge(Board):
    def __init__(self):
        from litex_boards.targets import antmicro_sdi_mipi_video_converter
        Board.__init__(self, antmicro_sdi_mipi_video_converter.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

    def load(self, soc, filename):
        prog = soc.platform.create_programmer(prog="ecpprog")
        prog.load_bitstream(filename)

#---------------------------------------------------------------------------------------------------
# LiteX Boards
#---------------------------------------------------------------------------------------------------

# Simulation ---------------------------------------------------------------------------------------

class LitexSim(Board):
    soc_kwargs = {
        "uart_name"         : "serial",
        "sim_config"        : SimConfig(),
        "integrated_main_ram_size": 0x10000,
    }
    def __init__(self):
        from litex.tools import litex_sim
        Board.__init__(self, litex_sim.SimSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "spiflash",
        })
        self.builder_kwargs["sim_config"] = self.soc_kwargs["sim_config"]

#---------------------------------------------------------------------------------------------------
# Build
#---------------------------------------------------------------------------------------------------

supported_boards = {
    # LiteX
    "litex_sim"                   : LitexSim,

    # Xilinx
    "arty"                        : Arty,

    # Lattice
    "sdi_mipi_bridge"             : SDI_MIPI_Bridge,
}

def main():
    description = "Zephyr on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in supported_boards.keys():
        description += "- " + name + "\n"
    from litex.soc.integration.soc import LiteXSoCArgumentParser
    parser = LiteXSoCArgumentParser(description="LiteX SoC on Arty A7 and SDI-MIPI Bridge")
    parser.add_argument("--toolchain", default="symbiflow", help="FPGA toolchain - vivado, symbiflow or oxide (yosys+nextpnr).")
    parser.add_argument("--board", required=True, help="FPGA board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--variant", default=None, help="FPGA board variant")
    parser.add_argument("--load", action="store_true", help="load bitstream (to SRAM). set path to bitstream")
    parser.add_argument("--sys-clk-freq", default=100e6, help="System clock frequency.")
    parser.add_argument("--spi-data-width", type=int, default=8,      help="SPI data width (maximum transfered bits per xfer)")
    parser.add_argument("--spi-clk-freq",   type=int, default=1e6,    help="SPI clock frequency")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")
    builder_args(parser)
    vivado_build_args(parser)
    oxide_args(parser)
    args = parser.parse_args()

    # Board(s) selection ---------------------------------------------------------------------------
    if args.board == "all":
        board_names = list(supported_boards.keys())
    else:
        args.board = args.board.lower()
        board_names = [args.board.replace(" ", "_")]

    for board_name in board_names:
        if board_name not in supported_boards:
            print("Board {} is not supported currently".format(board_name))
            continue
        board = supported_boards[board_name]()
        soc_kwargs = Board.soc_kwargs
        soc_kwargs.update(board.soc_kwargs)
        soc_kwargs.update(toolchain=args.toolchain)
        soc_kwargs.update(with_jtagbone=False)

        # SoC parameters ---------------------------------------------------------------------------
        if args.variant is not None:
            soc_kwargs.update(variant=args.variant)
        if args.sys_clk_freq is not None:
            soc_kwargs.update(sys_clk_freq=int(float(args.sys_clk_freq)))

        # SoC creation -----------------------------------------------------------------------------
        soc = SoCZephyr(board.soc_cls, **soc_kwargs)

        # SoC peripherals --------------------------------------------------------------------------
        if "ethernet" in board.soc_capabilities:
            soc.add_eth(local_ip=args.local_ip, remote_ip=args.remote_ip)
        if "mmcm" in board.soc_capabilities:
            soc.add_mmcm(board.mmcm_freq)
        if "rgb_led" in board.soc_capabilities:
            soc.add_rgb_led()
        if "spi" in board.soc_capabilities:
            soc.add_spi(args.spi_data_width, args.spi_clk_freq)
        if "i2c" in board.soc_capabilities:
            soc.add_i2c()
        if "i2s" in board.soc_capabilities:
            soc.add_i2s()

        if args.build:
            builder = Builder(soc, **builder_argdict(args))
            builder_kwargs = board.builder_kwargs
            if args.toolchain == "vivado":
                builder_kwargs.update(vivado_build_argdict(args))
            elif args.toolchain == "oxide":
                builder_kwargs.update(oxide_argdict(args))
            builder.build(**builder_kwargs, run=args.build)

        if args.load:
            board.load(filename=builder.get_bitstream_filename(mode="sram"))

if __name__ == "__main__":
    main()
