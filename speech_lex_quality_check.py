#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Guenter Bartsch
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
# check for lex entries that do not meet our quality standards,
# - currently we only check for stress markers (at least one is required per entry)
#

import os
import sys
import logging
import traceback
import locale
import codecs

from optparse               import OptionParser

from nltools                import misc
from speech_lexicon         import Lexicon

PROC_TITLE = 'speech_lex_quality_check'
NUM_TOKENS = 40

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

#
# check
#

cnt = 0

failed_tokens = []

for token in lex:

    if token == u'nspc':
        continue

    entry = lex[token]

    ipa = entry['ipa']

    failed = None

    if not (u"'" in ipa):
        failed = 'no stress marker'

    if u"--" in ipa:
        failed = 'double stress marker'

    c_prev  = None
    for c in ipa:
        if c_prev==u'ʔ' and c == u'-':
            failed = u'ʔ- found'
        if c_prev != u"-" and c_prev and c == u"'":
            failed = "stress not at beginning of syllable"
        c_prev = c

    if len(ipa) == 0:
        failed = "empty"

    if not failed:
        continue

    cnt += 1
    print cnt, token, ipa, failed

    failed_tokens.append(token)

#
# output
#

print "./speech_lex_edit.py", 

for token in failed_tokens[:NUM_TOKENS]:
    print token,

