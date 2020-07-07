#!/usr/bin/env python3

import argparse
import os

from litex.soc.integration.builder import Builder

from soc_zephyr import SoCZephyr

# Board definition----------------------------------------------------------------------------------

class Board:
    def __init__(self, soc_cls):
        self.soc_cls = soc_cls
        self.mmcm_freq = {}

    def load(self):
        raise NotImplementedError

    def flash(self):
        raise NotImplementedError

# Arty support -------------------------------------------------------------------------------------

class Arty(Board):
    def __init__(self):
        from litex_boards.targets import arty
        Board.__init__(self, arty.BaseSoC)
        self.mmcm_freq = {
            "i2s_rx" :  11.289e6,
            "i2s_tx" :  22.579e6,
        }

    def load(self):
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg")
        prog.load_bitstream("build/arty/gateware/arty.bit")

    def flash(self):
        flash_regions = {
            "buildroot/Image.fbi":             "0x00000000", # Linux Image: copied to 0xc0000000 by bios
            "buildroot/rootfs.cpio.fbi":       "0x00500000", # File System: copied to 0xc0800000 by bios
            "buildroot/rv32.dtb.fbi":          "0x00d00000", # Device tree: copied to 0xc1000000 by bios
            "emulator/emulator.bin.fbi":       "0x00e00000", # MM Emulator: copied to 0x20000000 by bios
        }
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg",
            flash_proxy_basename="prog/bscan_spi_xc7a35t.bit")
        prog.set_flash_proxy_dir(".")
        for filename, base in flash_regions.items():
            base = int(base, 16)
            print("Flashing {} at 0x{:08x}".format(filename, base))
            prog.flash(base, filename)

# Main ---------------------------------------------------------------------------------------------

supported_boards = {
    # Xilinx
    "arty":         Arty,
}

def main():
    description = "Zephyr on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in supported_boards.keys():
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board", required=True, help="FPGA board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (to SRAM)")
    parser.add_argument("--flash", action="store_true", help="flash bitstream/images (to SPI Flash)")
    parser.add_argument("--with_ethernet", action="store_true", help="Enable ethernet")
    parser.add_argument("--with_i2s", action="store_true", help="Enable i2s")
    parser.add_argument("--with_mmcm", action="store_true", help="Enable mmcm")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")
    args = parser.parse_args()

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
        soc_kwargs = {"integrated_rom_size": 0xfa00}
        soc = SoCZephyr(board.soc_cls, **soc_kwargs)
        if args.with_ethernet:
            soc.add_eth(local_ip=args.local_ip, remote_ip=args.remote_ip)
        if args.with_mmcm:
            soc.add_mmcm(board.mmcm_freq)
        if args.with_i2s:
            if not args.with_mmcm:
                print("Adding mmcm implicitly, cause i2s core needs special clk signals")
                soc.add_mmcm(board.mmcm_freq)
            soc.add_i2s()

        build_dir = os.path.join("build", board_name)
        if args.build:
            builder = Builder(soc, output_dir=build_dir,
                csr_json=os.path.join(build_dir, "csr.json"))
        else:
            builder = Builder(soc, output_dir="build/" + board_name,
                compile_software=True, compile_gateware=False,
                csr_json=os.path.join(build_dir, "csr.json"))
        builder.build()

        if args.load:
            board.load()

        if args.flash:
            board.flash()

if __name__ == "__main__":
    main()
