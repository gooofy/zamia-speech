#!/usr/bin/env python
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
# export speech training data to create a wav2letter case
#

import sys
import logging
import os
import codecs

from optparse               import OptionParser

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa

from speech_lexicon         import Lexicon
from speech_transcripts     import Transcripts

APP_NAME            = 'gspv2_mic_accept'
AUDIO_CORPUS        = 'gspv2'

#
# main
#

misc.init_app(APP_NAME)

#
# commandline
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# load transcripts
#

logging.info ('loading transcripts from %s ...' % AUDIO_CORPUS)
transcripts = Transcripts(corpus_name=AUDIO_CORPUS)
logging.info ('loading transcripts from %s ... done.' % AUDIO_CORPUS)

#
# build set of accepted submissions
#

accept = set()
mics = set (['Kinect-RAW', 'Realtek', 'Samson', 'Yamaha', 'Kinect-Beam'])
for utt_id in transcripts:

    data = transcripts[utt_id]
    if data['quality'] < 2:
        continue

    parts = utt_id.split('-')

    n = len(parts)
    mic = '-'.join(parts[n-1:])

    if not mic in mics:
        mic = '-'.join(parts[n-2:])
        if not mic in mics:
            logging.error('unknown mic: %s' % mic)
            continue

    logging.debug('%s -> mic=%s' % (utt_id, mic))

    accept.add(utt_id.replace(mic,''))

#
# apply to corresponding submissions that use other mics
#

cnt = 0
for utt_id in transcripts:

    data = transcripts[utt_id]
    if data['quality'] != 0 :
        continue

    parts = utt_id.split('-')

    n = len(parts)
    mic = '-'.join(parts[n-1:])

    if not mic in mics:
        mic = '-'.join(parts[n-2:])
        if not mic in mics:
            logging.error('unknown mic: %s' % mic)
            continue

    logging.debug('%s -> mic=%s' % (utt_id, mic))

    base_utt_id = utt_id.replace(mic, '')

    if base_utt_id in accept:
        cnt += 1
        logging.info('accepting utt #%5d : %s' % (cnt, utt_id))

        transcripts[utt_id]['quality'] = 2
        transcripts[utt_id]['ts']      = u' '.join(tokenize(transcripts[utt_id]['prompt'], lang='de', keep_punctuation=True))

logging.info("saving transcripts...")
transcripts.save()
logging.info("saving transcripts...done.")

