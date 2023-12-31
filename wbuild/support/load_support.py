# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>


import os
import sys
import subprocess
import shutil
import time

from waflib import Errors, Logs


def load_ram(ctx):
    """
    The program_openocd fuction just calls the OpenOCD debugger, passing the built ELF file, which is directly loaded
    into RAM after a 10s timeout to allow the user to reboot/push the programming button on the hardware board.

    Args:
        :param ctx: The WAF context
    """
    elf_path = os.path.join('build/' + ctx.variant + '/' + ctx.env.name + '.elf')
    if os.path.exists(elf_path):
        Logs.pprint('RED', '\n########################\n' + \
                    'HOLD PROGRAMMING BUTTON\n' + \
                    '########################\n')

        # Use red color for the STDOUT
        sys.stdout.write("\033[1;31m")
        for remaining in range(10, -1, -1):
            sys.stdout.write('\r')
            sys.stdout.write('Programming in {:2d}'.format(remaining)),
            sys.stdout.flush()
            time.sleep(1)

        Logs.pprint('RED', '\n\n#####\n\n Programming Hardware board\n\n#####\n\n')
        subprocess.call(''.join(ctx.env.OPENOCD) + ' ' + ''.join(ctx.env.OPENOCD_ARGS) +
                        ' & ' + ''.join(ctx.env.GDB) + ' --nh ' + elf_path
                        + ''.join(ctx.env.GDB_OPENOCD_FLAGS), shell=True)

        Logs.pprint('GREEN', '\n\n#####\n\n Programming completed\n\n#####\n\n')
    else:
        ctx.fatal('You need to build the application before being able to program it')


def load_envm(ctx):
    """
    The program_fpgenprog function just calls the fpgenprog binary, with the required steps to program the ENVM memory.
    The steps which are run in this function have been reverse engineered from mpfsbootmodeprogrammer jar which is
    ship with Softconsole IDE.

    Args:
        :param ctx: The WAF context
    """
    if os.path.exists('build/' + ctx.variant + '/' + ctx.env.name + '-bm1-p0.hex'):
        Logs.pprint('RED', '\n########################\n' + \
                    'PROGRAMMING ENVM MEMORY\n' + \
                    '########################\n')
        Logs.pprint('RED', 'Be patient. This process can take up to 30 seconds\n')

        # Define the path of the new fpgenprog project
        fpgenproject_dir_path = os.path.join('build/' + ctx.variant + '/' + '/fpgenprogProject')

        # We need the abspath of fpgenprject dir due to an fpgenprog bug in generate_bitstream step.
        # In particular, it seems like fpgenprog is not able to work with relative paths in this step.
        fpgenproject_dir_path = os.path.abspath(fpgenproject_dir_path)

        # Target Die of SoC
        target_die = 'MPFS25T_ES'

        # Target package of the SoC
        target_package = 'FCV484'

        # Bootmode configuration
        mss_bootmode = str(1)

        # ENVM bootcfg magic
        mss_bootcfg = str(2022010020220100202201002022010020220100)

        # Start page of the client
        start_page = str(0)

        # ENVM client name
        client_name = 'bootmode1_0'

        # ENVM base address:
        envm_base_address = str(20220000)

        # Path of the ENVM client (so to speak, the bootloader), both binary and hex
        base_output_path = os.path.join('build/' + ctx.variant + '/' + ctx.env.name)
        bin_payload_path = os.path.join(base_output_path + '-bm1-p0.bin')
        hex_payload_path = os.path.join(base_output_path + '-bm1-p0.hex')

        # Compute the binary payload total size, will be passed to envm_client generation step
        payload_total_size = str(os.stat(bin_payload_path).st_size)

        # In cane the user is going to do several dirty build - we always need to regenerate the project, so make sure
        # eliminate the project folder if it exists
        if os.path.exists(fpgenproject_dir_path) and os.path.isdir(fpgenproject_dir_path):
            shutil.rmtree(fpgenproject_dir_path)

        # Actual ENVM programming steps. Don't mess with it if you don't exactly know what you are doing. It may eat
        # your cat!
        subprocess.call(''.join(ctx.env.FPGENPROG) + ' new_project --location ' + fpgenproject_dir_path +
                        ' --target_die ' + target_die +
                        ' --target_package ' + target_package,
                        shell=True)
        subprocess.call(''.join(ctx.env.FPGENPROG) + ' mss_boot_info --location ' + fpgenproject_dir_path +
                        ' --u_mss_bootmode ' + mss_bootmode +
                        ' --u_mss_bootcfg ' + mss_bootcfg,
                        shell=True)
        subprocess.call(''.join(ctx.env.FPGENPROG) + ' envm_client --location ' + fpgenproject_dir_path +
                        ' --number_of_bytes ' + payload_total_size +
                        ' --content_file_format intel-hex --content_file ' + hex_payload_path +
                        ' --start_page ' + start_page +
                        ' --client_name ' + client_name +
                        ' --mem_file_base_address ' + envm_base_address,
                        shell=True)
        subprocess.call(''.join(ctx.env.FPGENPROG) + ' generate_bitstream --location ' + fpgenproject_dir_path,
                        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                        shell=True)
        subprocess.call(''.join(ctx.env.FPGENPROG) + ' run_action --location ' + fpgenproject_dir_path +
                        ' --action PROGRAM',
                        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)
    else:
        ctx.fatal('You need to generate bootmode1 payload before being able to program the board')
