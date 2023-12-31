#!/bin/bash

# Based on SAMBA updater script for WAF
# Author: F. Cuzzocrea
# Date: 31/12/2023

# Sanity check on input
if [[ $# -lt 1 ]]; then
  echo "Usage: update.sh BRANCH"
  exit 1
fi

# Common variables
WAF_GIT="git@github.com:fcuzzocrea/waf.git"
WAF_BRANCH="${1}"
WAF_UPDATE_SCRIPT="$(readlink -f "$0")"
WAF_DBUILD_DIR="$(dirname "${WAF_UPDATE_SCRIPT}")"
WAF_TMPDIR=$(mktemp --tmpdir -d waf-XXXXXXXX)

# Output information
echo "GIT URL:        ${WAF_GIT}"
echo "GIT BRANCH:     ${WAF_BRANCH}"
echo "WAF DBUILD DIR: ${WAF_DBUILD_DIR}"
echo "WAF TMP DIR:    ${WAF_TMPDIR}"

cleanup_tmpdir() {
  popd 2>/dev/null || true
  rm -rf "$WAF_TMPDIR"
}
trap cleanup_tmpdir SIGINT

cleanup_and_exit() {
  cleanup_tmpdir
  if test "$1" = 0 -o -z "$1"; then
    exit 0
  else
    exit "$1"
  fi
}

# Checkout the git tree
mkdir -p "${WAF_TMPDIR}"
pushd "${WAF_TMPDIR}" || cleanup_and_exit 1

git clone "${WAF_GIT}" -b "${WAF_BRANCH}"
ret=$?
if [ $ret -ne 0 ]; then
  echo "ERROR: Failed to clone repository"
  cleanup_and_exit 1
fi

# Build WAF
pushd waf || cleanup_and_exit 1

python3 waf distclean configure build
ret=$?
if [ $ret -ne 0 ]; then
  echo "ERROR: Failed to build waf"
  cleanup_and_exit 1
fi

pushd "${WAF_DBUILD_DIR}" || cleanup_and_exit 1

# Copy build output to current dir, make it exectuable and add it to git
rsync -av "${WAF_TMPDIR}/waf/build/waf" .
ret=$?
if [ $ret -ne 0 ]; then
  echo "ERROR: Failed copy waf executable"
  cleanup_and_exit 1
fi
chmod +x waf

git add waf

popd || cleanup_and_exit 1

echo
echo "Built and updated waf successfully"
echo "Now please commit the updated version"
echo

cleanup_and_exit 0
