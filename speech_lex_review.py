#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# pick 20 lex entries where sequitur disagrees at random
#

import os
import sys
import logging
import traceback
import locale
import codecs
import random

from optparse import OptionParser

import utils

LANG = 'de'

INPUTFILE  = 'data/dst/speech/%s/sequitur/model-6-all.test' % LANG
NUM_TOKENS = 20

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

random.seed()

with codecs.open(INPUTFILE, 'r', 'utf8', 'ignore') as inf :

    tokens = []

    for line in inf:

        if not 'errors)' in line:
            continue

        if '(0 errors)' in line:
            continue

        token = line.split('\t')[0]
        tokens.append(token)


    picked = set()

    while len(picked) < NUM_TOKENS:

        picked.add(tokens[random.randint(0, len(tokens)-1)])

    for token in sorted(picked):
        print token.encode('utf8'),


