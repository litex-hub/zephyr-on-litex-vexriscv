Zephyr-on-litex-vexriscv
========================

Zephyr on LiteX VexRiscv is a LiteX SoC builder for `litex_vexriscv` platform in Zephyr. Currently it supports [Digilent Arty A7-35T Development Board](https://store.digilentinc.com/arty-a7-artix-7-fpga-development-board-for-makers-and-hobbyists).

Prerequisites
------------

First, you have to install F4PGA toolchain. It can be done by following instructions in [this tutorial](https://f4pga-examples.readthedocs.io/en/latest/getting.html).

Then, clone and enter Zephyr-on-litex-vexriscv repository:

```bash
git clone https://github.com/litex-hub/zephyr-on-litex-vexriscv.git && cd zephyr-on-litex-vexriscv
```

Get all required submodules, packages and run install script:
```bash
git submodule update --init --recursive
apt-get install build-essential bzip2 python3 python3-dev python3-pip
./install.sh
```

Build
-----
Build bitstream following these steps:

* Add LiteX to path:
```bash
source ./init
```
* Prepare F4PGA environment:
```bash
export INSTALL_DIR="path/to/f4pga"
FPGA_FAM="xc7"
export PATH="$INSTALL_DIR/$FPGA_FAM/install/bin:$PATH";
source "$INSTALL_DIR/$FPGA_FAM/conda/etc/profile.d/conda.sh"
conda activate $FPGA_FAM
```
* Finally build the bitstream:
```bash
./make.py --board=arty --build --toolchain=symbiflow
```

Build options
-----
| Option | Help |
|---|---|
| --toolchain | FPGA toolchain |
| --board | FPGA board |
| --build | build bitstream |
| --variant | FPGA board variant |
| --load | load bitstream |
| --with-ethernet | Enable ethernet |
| --with_i2s | Enable i2s |
| --sys-clk-freq | System clock frequency |
| --with_spi | Enable SPI |
| --with_i2c | Enable i2c |
| --with_pwm | Enabe PWM |
| --spi-data-width | SPI data width |
| --spi-clk-freq | SPI clock frequency |
| --with_mmcm | Enable MMCM |
| --local-ip | local IP address |
| --remote-ip | remote IP address |

Load bitstream
--------------
Connect your board using the serial port and load bitstream:

```bash
source ./init
./make.py --board=arty --load
```
