Zephyr-on-litex-vexriscv
========================

Zephyr on LiteX VexRiscv is a LiteX SoC builder for the `litex_vexriscv` platform in Zephyr. Currently it supports [Digilent Arty A7-35T Development Board](https://store.digilentinc.com/arty-a7-artix-7-fpga-development-board-for-makers-and-hobbyists) and [SDI MIPI Video Converter](https://github.com/antmicro/sdi-mipi-video-converter).

Prerequisites
------------

First, if you want to run Zephyr on Digilent Arty, you have to install the F4PGA toolchain. It can be done by following instructions in [this tutorial](https://f4pga-examples.readthedocs.io/en/latest/getting.html).
For SDI MIPI Video Converter - install oxide (yosys+nextpnr) toolchain by following [these instructions](https://github.com/gatecat/prjoxide#getting-started---complete-flow).

Then, clone and enter the Zephyr-on-litex-vexriscv repository:

```bash
git clone https://github.com/litex-hub/zephyr-on-litex-vexriscv.git && cd zephyr-on-litex-vexriscv
```

Get all required submodules and packages, and run the install script:
```bash
git submodule update --init --recursive
apt-get install build-essential bzip2 python3 python3-dev python3-pip
./install.sh
```

Build
-----
Build the bitstream by following these steps:

* Add LiteX to path:
```bash
source ./init
```
* Prepare F4PGA environment (for Digilent Arty target):
```bash
export F4PGA_INSTALL_DIR="path/to/f4pga"
FPGA_FAM="xc7"
export PATH="$F4PGA_INSTALL_DIR/$FPGA_FAM/install/bin:$PATH";
source "$F4PGA_INSTALL_DIR/$FPGA_FAM/conda/etc/profile.d/conda.sh"
conda activate $FPGA_FAM
```
* Finally build the bitstream:

    For Digilent Arty board:
    ```bash
    ./make.py --board=arty --build
    ```
    For SDI MIPI board:
    ```bash
    ./make.py --board=sdi_mipi_bridge --build --toolchain=oxide
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
| --with_spi_flash | Enable SPI flash |
| --with_i2c | Enable I2C (bitbang driver) |
| --with_litei2c | Enable I2C via [LiteI2C](https://github.com/litex-hub/litei2c) |
| --with_pwm | Enable PWM |
| --spi-data-width | SPI data width |
| --spi-clk-freq | SPI clock frequency |
| --spi_flash_rate | SPI flash rate |
| --with_mmcm | Enable MMCM |
| --local-ip | local IP address |
| --remote-ip | remote IP address |

Load bitstream
--------------
Connect your board using the serial port and load the bitstream:

For Digilent Arty board:
```bash
source ./init
./make.py --board=arty --load
```

For SDI MIPI board:
```bash
source ./init
./make.py --board=sdi_mipi_bridge --load
```
