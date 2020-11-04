Zephyr-on-litex-vexriscv
========================

Prerequisites
------------
Install the Vivado toolchain. You can download Vivado using this [link](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/archive.html). 
The 2017.3 or newer version of Vivado is recommended.  
Get all required submodules:

```bash
git submodule update --init --recursive
```

Get all required packages:
```bash
apt-get install build-essential bzip2 python3 python3-dev python3-pip
./install.sh
```

Build
-----
Build bitstream following these steps:

```bash
source ./init
source ${PATH_TO_VIVADO_TOOLCHAIN}/settings64.sh
./make.py --board=arty --build --with_mmcm --with_i2s --with_ethernet
```

Load bitstream
--------------
Connect your board using the serial port then,  
load bitstream following these steps:

```bash
source ./init
./make.py --board=arty --load
```
