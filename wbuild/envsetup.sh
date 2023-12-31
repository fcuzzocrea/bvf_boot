#!/bin/bash

# Author: F. Cuzzocrea
# Date: 31/12/2023

PROJECT_ROOT=$(pwd)
WAF_BIN=${PROJECT_ROOT}/wbuild/waf

croot() {
  cd "${PROJECT_ROOT}" || return
}

alias waf="python3 \${WAF_BIN}"

# Make sure we don't have any library preloaded.
unset LD_PRELOAD

# Make sure we get stable hashes - this is needed to avoid to rebuild the
# world in conscutive builds without a distclean.
# For details see the thread:
# https://lists.samba.org/archive/samba-technical/2018-December/131503.html
PYTHONHASHSEED=1
export PYTHONHASHSEED
export PATH="$PATH:$HOME/riscv-bare/bin"
export FPSERVER="/opt/fpServer/bin/fpServer"
export FPGENPROG="/opt/microchip/Libero_SoC_v2023.2/Libero/bin64/fpgenprog"

export croot
