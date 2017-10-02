#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017 Guenter Bartsch
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
# generate english training sentences for language models from these sources:
#
# - europarl english
# - cornell movie dialogs
# - web questions
# - yahoo answers

import sys
import re
import os
import traceback
import ConfigParser
import codecs
import logging
import json

from optparse          import OptionParser
from nltools.misc      import compress_ws, load_config, init_app
from nltools.tokenizer import tokenize

SENTENCEFN      = 'data/dst/speech/en/sentences.txt'
SENTENCES_STATS = 1000

DEBUG_LIMIT     = 0
# DEBUG_LIMIT     = 1000

#
# init 
#

init_app ('speech_sentences')

config = load_config ('.speechrc')

europarl       = config.get("speech", "europarl_en")
movie_dialogs  = config.get("speech", "cornell_movie_dialogs")
web_questions  = config.get("speech", "web_questions")
yahoo_answers  = config.get("speech", "yahoo_answers")

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# sentence extraction from corpora
#

num_sentences = 0

with codecs.open(SENTENCEFN, 'w', 'utf8') as outf:

    #
    # yahoo answers
    #

    for infn in os.listdir('%s/text' % yahoo_answers):

        logging.debug('yahoo answers: reading file %s' % infn)

        with codecs.open('%s/text/%s' % (yahoo_answers, infn), 'r', 'latin1') as inf:
            for line in inf:
                sentence = u' '.join(tokenize(line, lang='en'))
        
                if not sentence:
                    continue

                outf.write(u'%s\n' % sentence)

                num_sentences += 1
                if num_sentences % SENTENCES_STATS == 0:
                    logging.info ('yahoo answers: %8d sentences.' % num_sentences)

                if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                    logging.warn ('yahoo answers: debug limit reached, stopping.')
                    break

        if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
            logging.warn ('yahoo answers: debug limit reached, stopping.')
            break

    #
    # web questions
    #

    for infn in ['webquestions.examples.test.json', 'webquestions.examples.train.json']:
        with open('%s/%s' % (web_questions, infn), 'r') as inf:

            data = json.loads(inf.read())

            for a in data:

                sentence = u' '.join(tokenize(a['utterance'], lang='en'))
        
                if not sentence:
                    logging.warn ('web questions: skipping null sentence %s' % line)
                    continue

                outf.write(u'%s\n' % sentence)

                num_sentences += 1
                if num_sentences % SENTENCES_STATS == 0:
                    logging.info ('web questions: %8d sentences.' % num_sentences)

                if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                    logging.warn ('web questions: debug limit reached, stopping.')
                    break
        
    #
    # cornell movie dialogs
    #

    with codecs.open('%s/movie_lines.txt' % movie_dialogs, 'r', 'latin1') as inf:
        for line in inf:
            parts = line.split('+++$+++')
            if not len(parts) == 5:
                logging.warn('movie dialogs: skipping line %s' % line)
                continue

            sentence = u' '.join(tokenize(parts[4], lang='en'))
    
            if not sentence:
                logging.warn ('movie dialogs: skipping null sentence %s' % line)
                continue

            outf.write(u'%s\n' % sentence)

            num_sentences += 1
            if num_sentences % SENTENCES_STATS == 0:
                logging.info ('movie dialogs: %8d sentences.' % num_sentences)

            if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                logging.warn ('movie dialogs: debug limit reached, stopping.')
                break

    #
    # europarl
    #

    logging.info("adding sentences from europarl...")
    with codecs.open(europarl, 'r', 'utf8') as inf:
        for line in inf:

            sentence = u' '.join(tokenize(line, lang='en'))
    
            if not sentence:
                logging.warn ('europarl: skipping null sentence.')
                continue

            outf.write(u'%s\n' % sentence)

            num_sentences += 1
            if num_sentences % SENTENCES_STATS == 0:
                logging.info ('europarl: %8d sentences.' % num_sentences)

            if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                logging.warn ('europarl: debug limit reached, stopping.')
                break

logging.info('%s written.' % SENTENCEFN)

