# !/usr/bin/env python
# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

from __future__ import division

import re
import os

from waflib import Logs

from tools.mss_header_binder import bind_mss_header_to_bin


def post_build_stats(ctx) -> None:
    # The post_build_stats function prints some statistics relative to the ELF file which is being
    # built, in particular the output is:
    #
    #     ########################
    #     Size Informations Below
    #     ########################
    #
    #        text	   data	    bss	    dec	    hex	filename
    #      362442	  22686	1588936	1974064	 1e1f30	build/release/sysctrlapp.elf
    #
    #     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #       Uses [%]   Output Sections      Size [byte] (fill)        Memory
    #     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #          78.27   .bss                     1538872 (15)          LIM
    #           0.88   .data                      17396 (4)           LIM
    #           0.01   .entry                       278 (0)           LIM
    #           0.00   .htif                         16 (0)           LIM
    #           0.59   .opensbi                   49152 (0)           DDR_C_LOW_SCA_PRT
    #           0.00   .rela.dyn                      0 (0)           LIM
    #           2.31   .rodata                    45436 (655)         LIM
    #           0.05   .sbss                        912 (73)          LIM
    #           0.01   .sdata                       274 (7)           LIM
    #           0.25   .sdram                      5000 (0)           LIM
    #           0.02   .srodata                     328 (23)          LIM
    #          16.09   .text                     316400 (242)         LIM
    #
    #     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #       Used [%]   Memory               Size [byte] (used)
    #     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #          97.91   LIM                      1966080 (1924912)
    #           0.59   DDR_C_LOW_SCA_PRT        8388608 (49152)
    #
    #     ########################
    #
    # As post_build_stats depends on the ELF file, in order to avoid strange race conditions is a
    # good practice to add it as a post_fun.
    #
    # Example usage:
    #
    #     # Post built tasks
    #     ctx.add_post_fun(post_build_stats)
    #
    # Args:
    #     :param ctx: The WAF context

    Logs.pprint('YELLOW', '\n########################\n' +
                'Size Informations Below\n' +
                '########################\n')
    tilde = '~' * 77
    Logs.pprint('YELLOW', tilde)
    ctx.exec_command(''.join(ctx.env.SIZE) + ' ' + ctx.env.name + '.elf', cwd=ctx.variant_dir)

    mapfile_map = {
         'mem_conf': 'Memory Configuration',
         'linker_conf': 'Linker script and memory map'
     }

    def get_string(strno) -> str | None:
        if strno == '1':
            return mapfile_map['mem_conf']
        if strno == '2':
            return mapfile_map['linker_conf']
        return None

    memory = {}
    out_sect = {}

    # Regular expressions
    memory_re = re.compile(
        r'(?P<memName>\w+)\s+(?P<memOrig>0x[\da-fA-F]+)\s+(?P<memLgt>0x[\da-fA-F]+)')
    out_sect_re_one_line = re.compile(
        r'(?P<sectName>\.[\S.]+)\s+(?P<sectStart>0x[\da-fA-F]+)\s+(?P<sectSize>0x[\da-fA-F]+)')
    out_sect_re_two_lines1 = re.compile(r'(?P<sectName>\.[\S.]+)$')
    out_sect_re_two_lines2 = re.compile(
        r'\s+(?P<sectStart>0x[\da-fA-F]+)\s+(?P<sectSize>0x[\da-fA-F]+)')
    fill_re = re.compile(r' \*fill\*\s+(?P<fillAdd>0x[\da-fA-F]+)\s+(?P<fillLgt>0x[\da-fA-F]+)')

    with open('build/' + ctx.variant + '/' + ctx.env.name + '.map', 'r',
              encoding='utf-8') as map_file:
        scan_phase = ""

        # Keep track of last encountered output section
        last_out_sec = ""

        for line in map_file:

            # Recognise sections of the map file
            if line.startswith(get_string('1')):
                scan_phase = "scanMemories"
            elif line.startswith(get_string('2')):
                scan_phase = ""
            elif line.startswith('.'):
                scan_phase = "scanOutSections"

            # Analysis
            if "scanMemories" == scan_phase:
                line_match = memory_re.match(line)
                if line_match:
                    mem_name = line_match.groupdict()['memName']
                    memory[mem_name] = {}
                    memory[mem_name]['origin'] = int(line_match.groupdict()['memOrig'], 16)
                    memory[mem_name]['length'] = int(line_match.groupdict()['memLgt'], 16)
                    memory[mem_name]['used'] = 0

            elif "scanOutSections" == scan_phase:

                # Output section (one line)
                if out_sect_re_one_line.match(line):

                    match_result = out_sect_re_one_line.match(line).groupdict()
                    if match_result['sectName'] not in out_sect:
                        last_out_sec = str(match_result['sectName'])
                        out_sect[last_out_sec] = {}
                        out_sect[last_out_sec]['size'] = int(match_result['sectSize'], 16)
                        out_sect[last_out_sec]['start'] = int(match_result['sectStart'], 16)
                        out_sect[last_out_sec]['fill'] = 0

                # Output section (two lines)
                if out_sect_re_two_lines1.match(line):
                    match_result1 = out_sect_re_two_lines1.match(line).groupdict()
                    line = next(map_file)
                    if out_sect_re_two_lines2.match(line):
                        match_result2 = out_sect_re_two_lines2.match(line).groupdict()
                        last_out_sec = str(match_result1['sectName'])
                        out_sect[last_out_sec] = {}
                        out_sect[last_out_sec]['size'] = int(match_result2['sectSize'], 16)
                        out_sect[last_out_sec]['start'] = int(match_result2['sectStart'], 16)
                        out_sect[last_out_sec]['fill'] = 0

                # Filled bytes
                elif fill_re.match(line):
                    match_result = fill_re.match(line).groupdict()
                    out_sect[last_out_sec]['fill'] += int(match_result['fillLgt'], 16)

        # For every identified output section, add its size to the corresponding
        # memory
        for outSecName, sec_data in out_sect.items():
            sec_data['memory'] = ""
            for mem_name, memData in memory.items():
                if (sec_data['start'] >= memData['origin']) \
                        and (sec_data['start'] < (memData['origin'] + memData['length'])):
                    sec_data['memory'] = mem_name
                    memData['used'] += sec_data['size']

        # Print the resulting output sections information
        tilde = '~' * 77
        Logs.pprint('YELLOW', tilde)
        Logs.pprint('NORMAL', f'{"Uses [%]":>10s}{"   Output Sections":<20s}'
                              f'{"Size [byte]":>15s}{" (fill)":<15s}{"Memory":<15s}')
        Logs.pprint('YELLOW', tilde)

        # Sort all outSect keys
        sorted_out_sect = list(out_sect.keys())
        sorted_out_sect.sort()
        for outSectName in sorted_out_sect:
            sec_data = out_sect[outSectName]
            if sec_data['memory']:
                Logs.pprint('NORMAL',
                            f'{((100*sec_data["size"])/memory[sec_data["memory"]]["length"]):>10.2f}'
                            f'{"   " + outSectName:<20s}{sec_data["size"]:>15d}'
                            f'{" (" + str(sec_data["fill"]) + ")":<15s}{sec_data["memory"]}')

        # Print the resulting memories information
        tilde = '~' * 60
        Logs.pprint('YELLOW', '\n' + tilde)
        Logs.pprint('NORMAL', f'{"Used [%]":>10s}{"   Memory":<20s}'
                    f'{"Size [byte]":>15s}{" (used)":<15s}')
        Logs.pprint('YELLOW', tilde)
        for mem_name, memData in memory.items():
            if memData['used'] > 0:
                Logs.pprint('NORMAL', f'{(100 * memData["used"]) / memData["length"]:>10.2f}'
                            f'{"   " + mem_name:<20s}{memData["length"]:>15d}'
                            f'{" (" + str(memData["used"]) + ")":<15s}')
    Logs.pprint('YELLOW', tilde + '\n')


def prepend_mss_header(ctx) -> None:
    # The prepend_mss_header function preprends the MSS header to any ELF
    # file built with this build system.
    # For knowing what the MSS header is and how it is made, please refer to
    # the bind_mss_header_to_bin function documentation.
    #
    # As bind_mss_header_to_bin depends on the ELF file, in order to avoid
    # strange race conditions is a good practice to add it as a post_fun.
    #
    # Example usage:
    #
    #     # Post built tasks
    #     ctx.add_post_fun(bind_mss_header_to_bin)
    #
    # Args:
    #     :param ctx: The WAF context

    bind_mss_header_to_bin(os.path.join(ctx.variant_dir, ctx.env.name + '.bin'),
                           ''.join(ctx.env.OBJCOPY))
