#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017 Guenter Bartsch
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
# compute top-n missing words in lexicon from submissions,
# optionally generate phoneme transcriptions for those using sequitur
#

import os
import sys
import logging
import traceback
import curses
import curses.textpad
import locale
import codecs

from optparse               import OptionParser

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa, xsampa2ipa
from nltools.sequiturclient import sequitur_gen_ipa

from speech_transcripts     import Transcripts
from speech_lexicon         import Lexicon

SEQUITUR_MODEL  = 'data/models/sequitur-voxforge-%s-latest'

#
# init 
#

misc.init_app ('speech_lex_missing')

#
# command line
#

parser = OptionParser("usage: %prog [options] [filter])")

parser.add_option ("-g", "--generate", action="store_true", dest="generate", 
                   help="generate phoneme transcriptions using sequitur g2p")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")

parser.add_option ("-n", "--num-words", dest="num_words", type="int", default=50,
                   help="max number of missing words to report, default: 50")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    verbose=True
else:
    logging.basicConfig(level=logging.INFO)
    verbose=False

sequitur_model = SEQUITUR_MODEL % options.lang

#
# load lexicon, transcripts
#

logging.info("loading lexicon...")
lex = Lexicon(file_name=options.lang)
logging.info("loading lexicon...done.")

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=options.lang)
logging.info("loading transcripts...done.")

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

    for word in tokenize(ts['prompt'], lang=options.lang):

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

    if cnt > options.num_words:
        break

    if verbose:
        logging.info(u"Missing %4d times: %s" % (item[1], item[0]))
    else:
        logging.info(item[0].encode('utf8'))

    if options.generate:
        ipas = sequitur_gen_ipa (sequitur_model, item[0])
        logging.info(u"%4d/%4d generated lex entry: %s -> %s" % (cnt, options.num_words, item[0], ipas))
        lex[item[0]] = {'ipa': ipas}

logging.info("%d missing words total. %d submissions lack at least one word, %d are covered fully by the lexicon." % (len(missing), num_ts_lacking, num_ts_complete))

if options.generate:
    logging.info('saving lexicon...')
    lex.save()
    logging.info('saving lexicon...done.')


