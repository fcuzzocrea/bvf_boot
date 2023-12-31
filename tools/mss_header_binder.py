# !/usr/bin/python

# pylint: disable=invalid-name
#
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>
# Date: 31/12/2023

"""
MSS Header Binder
~~~~~~~

The mss_header_binder script is used to create a header definition for the
supplied binary file, if supported. This script requires two parameters:

        1. The BIN file we want to add a header to
        2. The path to objdump

This script will return a -bm1-p0.hex file which can be programmed on the hardware board either using Libero SoC or as
ENVM client or directly using the Microchip fpgenprog utility.

An example through command line:

 python3 mss_header_binder.py c3boot.bin riscv64-unknown-elf-objcopy

Note: This script can also be called as a python module in other scripts.
"""

import subprocess
import sys


def bind_mss_header_to_bin(file, objcopy):
    """
    Procedure which is done trough this function has been reverse engineered from mpfsbootmodeprogrammer jar source
    code. Once the bootloader binary file is created, we need to prepend to the bin a small header which tells the
    pre-boot firmware of the board to start the ENVM client in BOOTMODE 1. To know more about Polarfire SoC bootmode,
    please, have a look at Polarfire SoC official documentation.
    Once we have attached the header to the payload, we need to convert the whole thing to intel hex format, passing
    to objcopy the --change-section-lma *+0x20220000 parameter, where 0x20220000 is the ENVM base address.

    Args:
        file:           The binary file we want to add a header to
        objcopy:        Objcopy executable

    Returns:
        file:           A .hex file is created in the same directory where the supplied file lives

    Examples:
        bind_mss_header_to_bin('build/release/c3boot.bin'', 'riscv64-unknown-elf-objcopy')
    """
    # This has been reverse engineered from *-bm1-dummySbic.bin which is produced by fpgenprog tool.
    # If you need to extract it again:
    # import base64
    # with open("*-bm1-dummySbic.bin", "rb") as f:
    #     encodedFile = base64.b64encode(f.read())
    #     print(encodedFile.decode())
    # base64.b64decode(encodedFile)
    bootmode1 = b'o\x00\x00\x10\xf0\xf5\x01\x00\x00\x01" \x00\x01" \x00\x01" \x00' \
                b'\x01" \x00\x01" \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xffBOOT MODE 1 DUMMY SBIC' \
                b'\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00'

    # ENVM base address
    envm_base_address = str(20220000)

    # Strip extension from file to manipulate it in the following steps
    filename_wo_ext = file.rsplit('.', 1)[0]
    # Variable holding file names
    bootmode1_bin = filename_wo_ext + '-bm1-p0.bin'
    bootmode1_hex = filename_wo_ext + '-bm1-p0.hex'

    # Concatenate the bootloader bin with the MSS header
    with open(file, "rb") as old, \
            open(bootmode1_bin, "wb") as new:
        new.write(bootmode1)
        new.write(old.read())

    # This is utterly ugly, but I need to do it like this until I have the time to learn how to do it better
    subprocess.call(objcopy + ' -I binary -O ihex --change-section-lma *+0x' + envm_base_address + ' ' +
                    bootmode1_bin + ' ' + bootmode1_hex, shell=True)


# Allows us to use this python file as either a script or a module
if __name__ == "__main__":

    if len(sys.argv) < 3 or len(sys.argv) > 3:
        print("You must provide this with at least two parameters, read the documentation to understand how it works.")
        sys.exit(1)

    # Do sys argv handling here
    bind_mss_header_to_bin(sys.argv[1], sys.argv[2])
