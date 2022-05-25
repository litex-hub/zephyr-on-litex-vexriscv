#!/bin/bash
set -ex

pip3 install --user requests

TOOLS_DIR='tools'
CONDA_DIR="$TOOLS_DIR/conda"
if [[ -d "$CONDA_DIR" ]]
then
    exit 1
fi

mkdir -p "$CONDA_DIR"

wget --no-verbose --continue https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod a+x ./Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -p "$CONDA_DIR" -b -f || exit 2
rm ./Miniconda3-latest-Linux-x86_64.sh

export PATH="$CONDA_DIR/bin:$PATH"
conda config --system --set always_yes yes

conda install -c timvideos gcc-riscv64-elf-nostdc openocd
conda install meson
