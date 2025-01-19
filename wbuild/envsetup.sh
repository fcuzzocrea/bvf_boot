#!/bin/bash

# Author: F. Cuzzocrea
# Date: 04/10/2022

# ANSI colours escape codes
BOLD_RED="\033[1;31m"
BOLD_WHITE="\033[1;37m"
BOLD_CYAN="\033[1;36m"
BOLD_GREEN="\033[1;32m"
BOLD_YELLOW="\033[1;33m"
RESET="\033[0m"

# Define common messages
ERROR="${BOLD_RED}ERROR:${BOLD_WHITE}"
WARNING="${BOLD_YELLOW}WARNING:${BOLD_WHITE}"
INFO="${BOLD_GREEN}INFO:${BOLD_WHITE}"

echo -e "${INFO} Setting up your workspace...."

# Assumption: this script is executed from the top directory of our workspace
WORKSPACE_ROOT=$(pwd)

# If we do not recognize the workspace layout bail out
for directory in \
    "$WORKSPACE_ROOT/wbuild"
do
    if ! [ -d "$directory" ]; then
        echo -e "${ERROR} Either this script is being executed from a wrong location or a malformed workspace" \
                " has been found, required module ${BOLD_CYAN}$(basename "$directory")${BOLD_WHITE} is not present."
        break
        exit 1
    fi
done

if [ -z ${RISCV_TOOLCHAIN_PATH+x} ]; then
  echo -e "${WARNING} Baremetal toolchain path not specified, attempting to check if in the default path is present..."
  RISCV_TOOLCHAIN_PATH="/opt/riscv-unknown-elf-imac/bin";
  if [ -d "$RISCV_TOOLCHAIN_PATH" ]; then
    echo -e "${INFO} Baremetal toolchain installation found in the default path"
  else
    echo -e "${WARNING} Baremetal toolchain not found, you won't be able to build baremetal projects."
    RISCV_TOOLCHAIN_PATH=
  fi
fi

if [ -z ${RTEMS_TOOLCHAIN_PATH+x} ]; then
  echo -e "${WARNING} RTEMS 6 toolchain path not specified, attempting to check if in the default path is present..."
  RTEMS_TOOLCHAIN_PATH="/opt/riscv-rtems6/bin";
  if [ -d "$RTEMS_TOOLCHAIN_PATH" ]; then
    echo -e "${INFO} RTEMS 6 toolchain installation found in the default path"
    if [ -z ${RTEMS_BSP_PATH+x} ]; then
      echo -e "${WARNING} RTEMS 6 BSP path not specified, attempting to check if in the default path is present..."
      RTEMS_BSP_PATH="/opt/rtems/6/riscv-rtems6";
      if [ -d "$RTEMS_BSP_PATH" ]; then
        echo -e "${INFO} RTEMS 6 BSP installation found in the default path"
      else
        echo -e "${WARNING} RTEMS 6 BSP not found, you won't be able to build RTEMS projects."
        RTEMS_BSP_PATH=
      fi
    fi
  else
    echo -e "${WARNING} RTEMS 6 toolchain not found, you won't be able to build RTEMS projects."
    RTEMS_TOOLCHAIN_PATH=
  fi
fi

# Self generated file, for future usage
if ! [ -f WORKSPACE ]; then
cat <<EOF > WORKSPACE
### WARNING! WARNING! WARNING! SELF-GENERATED FILE, DO NOT EDIT ###
### WARNING! WARNING! WARNING! IT WILL EAT YOUR CAT ###

$(basename "$WORKSPACE_ROOT")
EOF
fi

# Setup the important paths which will then get exported
BUILD_SYSTEM_PATH=${WORKSPACE_ROOT}/wbuild

VENV_PATH=${WORKSPACE_ROOT}/wsenv
VENV_ACTIVATE_SCRIPT=${WORKSPACE_ROOT}/wsenv/bin/activate

# Setup virtual environment for the lazy (l)users
if ! [ -d "$VENV_PATH" ]; then
  # Create the virtual environment
  python -m venv "${VENV_PATH}"
fi

source "${VENV_ACTIVATE_SCRIPT}"

# Install requirements if necessary
arealdySetup=$(cat WORKSPACE | grep -c "VIRTUALENV_SETUP_DONE")

if [ "$arealdySetup" -eq 0 ]; then
  echo -e "${INFO} Installing build system requirements..."
  pip install -r "${BUILD_SYSTEM_PATH}"/requirements.txt
  echo "VIRTUALENV_SETUP_DONE" >> WORKSPACE
fi

# Convenience command to go to the top for our workspace from any directory
croot() {
  cd "${WORKSPACE_ROOT}" || return
}

# Make sure we don't have any library preloaded.
unset LD_PRELOAD

# Make sure we get stable hashes - this is needed to avoid to rebuild the
# world in conscutive builds without a distclean.
# For details see the thread:
# https://lists.samba.org/archive/samba-technical/2018-December/131503.html
PYTHONHASHSEED=1
export PYTHONHASHSEED

# For bind mounting for docker
export WORKSPACE_ROOT

# Export build system path to detect it if necessary
export BUILD_SYSTEM_PATH

# To allow build system to find the waftools
export BUILD_SYSTEM_PATH

# To allow python to find build system modules. This enable us to import wafbuild.xxx
export PYTHONPATH="${WORKSPACE_ROOT}"

# Create a global WAF command which invokes the right WAF version
WAF_BIN=${BUILD_SYSTEM_PATH}/waf
alias waf="python3 \${WAF_BIN}"

# Convenience command to reach worksapce root
export croot

# To avoid having map file in locale different than English
export LC_ALL=C

# Add all the discovered toolchains to the path.
if [[ -n "$RISCV_TOOLCHAIN_PATH" ]]; then
  [[ ":$PATH:" != *":$RISCV_TOOLCHAIN_PATH:"* ]] && PATH="$RISCV_TOOLCHAIN_PATH:${PATH}"
  export RISCV_TOOLCHAIN_PATH
fi

if [[ -n "$RTEMS_TOOLCHAIN_PATH" ]] && [[ -n "$RTEMS_BSP_PATH" ]]; then
  [[ ":$PATH:" != *":$RTEMS_TOOLCHAIN_PATH:"* ]] && PATH="$RTEMS_TOOLCHAIN_PATH:${PATH}"
  export RTEMSBSPROOT="$RTEMS_BSP_PATH"
  export RTEMS_TOOLCHAIN_PATH
fi

echo -e "${INFO} Workspace setup complete"
echo -e "${INFO} Remeber you are inside a virtualenv"
echo -e "${RESET}"
