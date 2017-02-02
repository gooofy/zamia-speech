#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016 Guenter Bartsch
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
# compute top-20 missing words in lexicon from submissions
#

import os
import sys
import logging
import traceback
import curses
import curses.textpad
import locale
import codecs

from optparse import OptionParser

import utils
from speech_transcripts import Transcripts
from speech_lexicon import Lexicon, ipa2xsampa, xsampa2ipa
from speech_tokenizer import tokenize

NUM_WORDS = 50

verbose = len(sys.argv)==2 and sys.argv[1] == '-v'

logging.basicConfig(level=logging.DEBUG)

#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

#
# load transcripts
#

transcripts = Transcripts()

#
# load lexicon
#

lex = Lexicon()

#
# find missing words
#

missing = {} # word -> count

num = len(transcripts)
cnt = 0

num_ts_lacking  = 0
num_ts_complete = 0

for cfn in transcripts:
    ts = transcripts[cfn]

    cnt += 1

    if ts['quality']>0:
        continue

    lacking = False

    for word in tokenize(ts['prompt']):

        if word in lex:
            continue

        if word in missing:
            missing[word] += 1
        else:
            missing[word] = 1
            #print u"%5d/%5d missing word: %s" % (cnt, num, word)

        lacking = True

    if lacking:
        num_ts_lacking += 1
    else:
        num_ts_complete += 1

cnt = 0
for item in reversed(sorted(missing.items(), key=lambda x: x[1])):

    cnt += 1

    if verbose:
        print u"Missing %4d times: %s" % (item[1], item[0])
    else:
        print item[0].encode('utf8'),
        if cnt > NUM_WORDS:
            break


if verbose:
    print
    print "%d missing words total. %d submissions lack at least one word, %d are covered fully by the lexicon." % (len(missing), num_ts_lacking, num_ts_complete)
    print

