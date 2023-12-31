# !/usr/bin/env python
# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import os


def clean_objects():
    """
    The clean_objects function can be used to remove all the objects generated in the build directory
    """
    os.system('rm build -r -f')
    os.system('rm build_current -r -f')
