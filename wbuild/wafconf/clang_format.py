#!/usr/bin/env python
# encoding: utf-8
# Francescodario Cuzzocrea 2022

from waflib.Configure import conf
from waflib import Task, TaskGen

clang_format_options = []

@conf
def find_clang_format(conf):
    conf.find_program('clang-format', var='CLANGFORMAT', mandatory=False)

def configure(conf):
    conf.find_clang_format()
    conf.env.append_unique('CLANG_FORMAT_OPTIONS', clang_format_options)


class clang_format(Task.Task):
    #: str: color in which the command line is displayed in the terminal
    color = 'BLUE'
    vars = ['CLANG_FORMAT_OPTIONS', 'CLANG_FORMAT_CONFIGURATION_FILES']
    run_str = '${CLANG_FORMAT} ${CLANG_FORMAT_OPTIONS} ${SRC[0].abspath()}'


@TaskGen.feature('clang-format')
def process_clang_format(self):
    if not getattr(self, 'files', None):
        self.bld.fatal('No files given.')
    for src in self.files:
        self.create_task('clang_format', src, cwd=self.path)
