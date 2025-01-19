# !/usr/bin/env python
# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods, missing-function-docstring
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>
# Date: 10/05/2024

import os
import subprocess
import tempfile
import shutil

from waflib.Build import BuildContext
from waflib import Logs


def format_srcs(ctx) -> None:
    # The format command is used to run clang-format.
    # To use this target simply import this function in you wscript
    # (from wafbuild.helpers.format_helpers import format_srcs) and
    # add the corresponding options if you are not using common app
    # options.
    #
    # Then this can be used from the command line using the following
    # syntax:
    #
    #        waf configure format_srcs
    #
    # Args:
    #     :param ctx: The WAF context

    if not ctx.env.CLANGFORMAT:
        ctx.fatal('In order to format source files you need to install clang-format')

    # Parse the sources of the application
    srcs = []
    for root, dirs, files in os.walk(ctx.path.get_bld().relpath()):
        for file in files:
            dirs[:] = [d for d in dirs if d != 'build']
            if file.endswith(('.c', '.h')):
                srcs.append(os.path.join(root, file))

    cmd = ''.join(ctx.env.CLANGFORMAT)

    if ctx.options.format_behaviour in ('dry-run', 'inplace-edit'):
        cmd = cmd +  ' --files= ' + ' '.join(srcs) + \
              ' -style=file ' + ' --color=1'
        if ctx.options.format_behaviour == 'dry-run':
            cmd = cmd + ' --dry-run'
        elif ctx.options.format_behaviour == 'inplace-edit':
            cmd = cmd + ' -i'
        ctx.exec_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    elif ctx.options.format_behaviour == 'generate-patch':
        cmd = cmd + ' -i '
        patch_content = []

        with tempfile.TemporaryDirectory() as tempdir:
            for file in srcs:
                # Copy the original file to a temporary location
                original_file = os.path.join(tempdir, os.path.basename(file))
                shutil.copy2(file, original_file)

                # Format the file in place
                ctx.exec_command(cmd + file)

                # Generate the diff
                diff = subprocess.run(['diff', '-u', original_file, file],
                                      capture_output=True, text=True, check=False)
                if diff.stdout:
                    patch_content.append(diff.stdout)

                # Restore the original file
                shutil.copy2(original_file, file)

        # Save the patch content to a file
        patch_file_path = os.path.join(ctx.path.get_bld().relpath(), 'build', 'clang_format.patch')
        if patch_content:
            with open(patch_file_path, 'w', encoding='utf-8') as patch_file:
                patch_file.writelines(patch_content)
            Logs.pprint('CYAN', 'Coding style violations found, '
                        f'patch file created: {patch_file_path}')
        else:
            Logs.pprint('CYAN', 'Code style all good.')



class FormatSrcs(BuildContext):
    '''format sources with clang-format by requests'''
    cmd = 'format_srcs'
    fun = 'format_srcs'
