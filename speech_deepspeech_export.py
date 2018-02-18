#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017, 2018 Guenter Bartsch
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
# export speech training data for mozilla deepspeech
#

import os
import sys
import logging
import traceback
import codecs

from optparse               import OptionParser
from StringIO               import StringIO

from nltools                import misc
from nltools.tokenizer      import tokenize

from speech_transcripts     import Transcripts

WORKDIR             = 'data/dst/speech/%s/deepspeech'
MIN_QUALITY         = 2
P_DEV               = 5 # use 5% for dev dataset
P_TEST              = 5 # use 5% for test dataset
PROMPT_AUDIO_FACTOR = 1000
#
# init 
#

misc.init_app ('speech_deepspeech_export')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0,
                   help="limit number of transcripts (debug purposes only), default: 0 (unlimited)")
parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")
parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

work_dir    = WORKDIR %options.lang 

wav16_dir   = config.get("speech", "wav16_dir_%s" % options.lang)

#
# load transcripts
#

logging.info ( "loading transcripts...")
transcripts = Transcripts(lang=options.lang)
logging.info ( "loading transcripts...done. %d transcripts." % len(transcripts))

#
# count good submissions
#

total_good = 0
for cfn in transcripts:
    ts = transcripts[cfn]
    if ts['quality'] < MIN_QUALITY:
        continue
    total_good += 1

#
# create work_dir 
#

misc.mkdirs('%s' % work_dir)

# /home/bofh/projects/ai/mozilla/DeepSpeech/data/librivox/LibriSpeech/dev-clean-wav/2277-149897-0004.wav,183564,he was getting some vague comfort out of a good cigar but it was no panacea for the ill which affected him


csv_train_fn = '%s/train.csv' % work_dir
csv_dev_fn   = '%s/dev.csv'   % work_dir
csv_test_fn  = '%s/test.csv'  % work_dir

alphabet = set()

with codecs.open(csv_train_fn, 'w', 'utf8') as csv_train_f, \
     codecs.open(csv_dev_fn  , 'w', 'utf8') as csv_dev_f, \
     codecs.open(csv_test_fn , 'w', 'utf8') as csv_test_f:

    csv_train_f.write('wav_filename,wav_filesize,transcript\n')
    csv_dev_f.write('wav_filename,wav_filesize,transcript\n')
    csv_test_f.write('wav_filename,wav_filesize,transcript\n')

    cnt_train = 0
    cnt_dev   = 0
    cnt_test  = 0
    cnt_all   = 0

    for cfn in transcripts:
        ts = transcripts[cfn]

        if ts['quality'] < MIN_QUALITY:
            continue

        wavfn  = '%s/%s.wav' % (wav16_dir, cfn)
        wavlen = os.path.getsize(wavfn)
        prompt = ts['ts']

        if (len(prompt)*PROMPT_AUDIO_FACTOR) > wavlen:
            logging.warn('Skipping %s (wav (%d bytes) too short for prompt (%d chars)' % (cfn, wavlen, len(prompt)))
            continue

        for c in prompt:
            alphabet.add(c)

        if cnt_dev < (cnt_all * P_DEV / 100):
            csv_dev_f.write('%s,%d,%s\n' % (wavfn, wavlen, prompt))
            cnt_dev += 1
        elif cnt_test < (cnt_all * P_TEST / 100):
            csv_test_f.write('%s,%d,%s\n' % (wavfn, wavlen, prompt))
            cnt_test += 1
        else:
            csv_train_f.write('%s,%d,%s\n' % (wavfn, wavlen, prompt))
            cnt_train += 1

        cnt_all = cnt_dev + cnt_test + cnt_train

logging.info ("%s %d lines written." % (csv_train_fn, cnt_train) )
logging.info ("%s %d lines written." % (csv_dev_fn, cnt_dev) )
logging.info ("%s %d lines written." % (csv_test_fn, cnt_test) )

alphabet_fn = '%s/alphabet.txt' % work_dir

with codecs.open(alphabet_fn, 'w', 'utf8') as alphabet_f:

    for c in sorted(alphabet):
        alphabet_f.write('%s\n' % c)
logging.info ("%s written." % alphabet_fn)


