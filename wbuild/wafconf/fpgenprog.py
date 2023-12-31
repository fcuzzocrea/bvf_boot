#!/usr/bin/env python
# encoding: utf-8
# Francescodario Cuzzocrea 2023

from waflib.Configure import conf


@conf
def find_fpgenprog(conf):
    conf.find_program("fpgenprog", var="FPGENPROG", mandatory=False)


def configure(conf):
    conf.find_fpgenprog()
