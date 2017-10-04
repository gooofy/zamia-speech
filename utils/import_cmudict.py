#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2017 Guenter Bartsch
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
# convert cmudict into our IPA based dictionary format
#
# WARNING: this is a very crude script, use with care!
#

import argparse
import os
import codecs
import re
import logging

from optparse          import OptionParser
from nltools           import misc, phonetics
from nltools.tokenizer import tokenize

PROC_TITLE='import_cmudict'

CMUDICT  = 'data/src/speech/en/cmudict-0.7b'
OUTDICT  = 'data/src/speech/en/dict.ipa'

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# arpabet -> xsampa translation dict
#

ab2xs = {}

for entry in phonetics.xs2xa_table:
    ab2xs[entry[1]] = entry[0]

ab2xs['OW'] = 'oU'
ab2xs['EY'] = 'eI'
ab2xs['UW'] = 'u'

#
# main
#

cnt     = 0
skipped = 0
with codecs.open(OUTDICT, 'w', 'utf8') as outf:
    with codecs.open(CMUDICT, 'r', 'latin1') as cmuf:

        for line in cmuf:

            if not line or line[0] == ';':
                continue

            parts = line.split()
            word = parts[0].lower()
            
            if '(' in word:
                word = word.replace('(', '_').replace(')', '')
                stem = word[0:len(word)-2]
            else:
                stem = word

            tk = tokenize(stem, lang='en')[0]
            if stem != tk:
                logging.warn ('# tokenizer diff: %s vs %s' % (repr(stem), repr(tk)))
                skipped += 1
                continue

            xs = ''
            for phone in parts[1:]:

                ph = phone
                if ph.endswith('0'):    
                    # xs += "'"
                    ph = ph[0:len(ph)-1]
                if ph.endswith('1'):    
                    xs += "'"
                    ph = ph[0:len(ph)-1]
                if ph.endswith('2'):    
                    # xs += "'"
                    ph = ph[0:len(ph)-1]

                if ph in ab2xs:
                    xs += ab2xs[ph]

                else:
                    logging.error ('unknown phone: %s' % ph)
                    sys.exit(1)

            ipa = phonetics.xsampa2ipa(word, xs)

            # print line.strip(), ' -> ', word, xs
            outf.write(u'%s;%s\n' % (word, ipa))
            cnt += 1

logging.info ('%d entries written to %s . skipped: %d' % (cnt, OUTDICT, skipped))


