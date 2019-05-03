#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Copyright 2019 Guenter Bartsch
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
# collect results from w2l auto-review, apply them to our transcripts
#

import sys
import logging
import os
import codecs
import re

from optparse               import OptionParser

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa

from speech_lexicon         import Lexicon
from speech_transcripts     import Transcripts

APP_NAME            = 'wav2letter_apply_review'

WORK_DIR            = 'tmp/w2letter_auto_review'

#
# main
#

misc.init_app(APP_NAME)

#
# commandline
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de', help="language (default: de)")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config ('.speechrc')

#
# collect results
#

corpora = {}
 
pattern = re.compile(r'^\[sample: (\d+), WER: ([0-9.]+)%,')

cnt = 0

with codecs.open('%s/logs/.log' % WORK_DIR, 'r', 'utf8') as logf:
    for line in logf:

        m = pattern.match(line)
        if not m: 
            continue

        sample = int(m.group(1))
        wer = float(m.group(2))

        # logging.debug('sample: %d, wer: %f' % (sample, wer))

        # read metadata of sample

        metafn = '%s/data/test/%09d.id' % (WORK_DIR, sample)
        meta = {}
        with codecs.open(metafn, 'r', 'utf8') as metaf:
            for line in metaf:
                parts = line.strip().split('\t')
                meta[parts[0]] = parts[1]

        utt_id = meta['utt_id']
        corpus = meta['corpus']
        lang   = meta['lang']

        quality = 0

        if wer == 0:
            quality = 1 # poort
        elif wer == 100:
            quality = 2 # fair
        else:
            continue # do not apply review

        logging.debug('%s WER=%f (corpus=%s, lang=%s)' % (utt_id, wer, corpus, lang))

        if not corpus in corpora:
            logging.info("loading transcripts for %s ..." % corpus)
            transcripts = Transcripts(corpus_name=corpus)
            logging.info("loading transcripts for %s ...done." % corpus)
            corpora[corpus] = transcripts
        else:
            transcripts = corpora[corpus]
    
        transcripts[utt_id]['quality'] = quality
        transcripts[utt_id]['ts']      = u' '.join(tokenize(transcripts[utt_id]['prompt'], lang=lang, keep_punctuation=True))

        cnt += 1

logging.info ('results applied to %d transcripts.' % cnt)

logging.info("saving transcripts...")
transcripts.save()
logging.info("saving transcripts...done.")

