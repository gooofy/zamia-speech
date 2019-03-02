#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017, 2018, 2019 Guenter Bartsch
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

SEQUITUR_MODEL  = 'data/models/sequitur-%s-latest'

#
# init 
#

misc.init_app ('speech_lex_missing')

#
# command line
#

parser = OptionParser("usage: %prog [options] [filter] lex corpus")

parser.add_option ("-g", "--generate", action="store_true", dest="generate", 
                   help="generate phoneme transcriptions using sequitur g2p")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")

parser.add_option ("-n", "--num-words", dest="num_words", type="int", default=50,
                   help="max number of missing words to report, default: 50")

parser.add_option ("-i", "--ignore-rating", action="store_true", dest="ignore_rating", 
                   help="check all submissions (ignore rating)")

parser.add_option ("-o", "--output-file", dest="output_file", type = "str",
                   help="append missing words to this file (default: no output file is written)")

parser.add_option ("-O", "--max-occurences", dest="max_occurences", type="int",
                   help="generate phonemes only for rare words up to the specified number of occurences, default: no limit")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

parser.add_option ("-w", "--wiktionary", dest="wiktionaryfn", type = "str",
                   help="only generate phoneme transcriptions for words present in wiktionary (default: no check against wiktionary)")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    verbose=True
else:
    logging.basicConfig(level=logging.INFO)
    verbose=False

if len(args)<2:
    parser.print_usage()
    sys.exit(1)

lex_name    = args[0]
corpus_name = args[1]

sequitur_model = SEQUITUR_MODEL % lex_name

#
# load lexicon, transcripts
#

wiktionary = None
if options.wiktionaryfn:
    logging.info("loading wiktionary...")
    wiktionary = set()
    with codecs.open(options.wiktionaryfn, 'r', 'utf8') as wiktionaryf:
        for line in wiktionaryf:
            wiktionary.add(line.strip().lower())
    logging.info ('%d words loaded from wiktionary' % len(wiktionary))

logging.info("loading lexicon...")
lex = Lexicon(file_name=lex_name)
logging.info("loading lexicon...done.")

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=corpus_name)
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

    if not options.ignore_rating:
        if ts['quality']>0:
            continue

    lacking = False

    # debug only
    # do_trace = True if 'snatcher' in ts['prompt'] else False
    do_trace = False

    for word in tokenize(ts['prompt'], lang=options.lang):

        if word in lex:
            if do_trace:
                logging.debug('word %s is in lex.' % word)
            continue

        if do_trace:
            logging.debug('word %s is in missing.' % word)

        if word in missing:
            missing[word] += 1
        else:
            missing[word] = 1
            logging.debug (u"%s: Missing word '%s' from '%s'" % (cfn, word, ts['prompt']))
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

    logging.info(u"Missing %4d times: %s" % (item[1], item[0]))

    if options.output_file:
        with codecs.open(options.output_file, 'a', 'utf8') as outf:
            outf.write(u'%s\n' % item[0])

    if options.generate:

        if wiktionary:
            if not item[0] in wiktionary:
                logging.info(u"%4d/%4d not generating phonemes for entry %s because it is not covered by wiktionary" % (cnt, options.num_words, item[0]))
                continue

        if options.max_occurences:
            if item[1] > options.max_occurences:
                logging.info(u"%4d/%4d not generating phonemes for entry %s because it is too common" % (cnt, options.num_words, item[0]))
                continue

        ipas = sequitur_gen_ipa (sequitur_model, item[0])
        logging.info(u"%4d/%4d generated lex entry: %s -> %s" % (cnt, options.num_words, item[0], ipas))
        lex[item[0]] = {'ipa': ipas}


logging.info("%d missing words total. %d submissions lack at least one word, %d are covered fully by the lexicon." % (len(missing), num_ts_lacking, num_ts_complete))

if options.generate:
    logging.info('saving lexicon...')
    lex.save()
    logging.info('saving lexicon...done.')


