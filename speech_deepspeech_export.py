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
transcripts = Transcripts(corpus_name=options.lang)
logging.info ( "loading transcripts...done. %d transcripts." % len(transcripts))
logging.info ("splitting transcripts...")
ts_all, ts_train, ts_test = transcripts.split()
logging.info ("splitting transcripts done, %d train, %d test." % (len(ts_train), len(ts_test)))

#
# create work_dir 
#

misc.mkdirs('%s' % work_dir)

# export csv files

csv_train_fn = '%s/train.csv' % work_dir
csv_dev_fn   = '%s/dev.csv'   % work_dir
csv_test_fn  = '%s/test.csv'  % work_dir

alphabet = set()
vocabulary = []

def export_ds(ds, csv_fn):

    global alphabet

    cnt = 0
    with codecs.open(csv_fn, 'w', 'utf8') as csv_f:

        csv_f.write('wav_filename,wav_filesize,transcript\n')


        for cfn in ds:
            ts = ds[cfn]

            wavfn  = '%s/%s.wav' % (wav16_dir, cfn)
            wavlen = os.path.getsize(wavfn)
            prompt = ts['ts']

            if (len(prompt)*PROMPT_AUDIO_FACTOR) > wavlen:
                logging.warn('Skipping %s (wav (%d bytes) too short for prompt (%d chars)' % (cfn, wavlen, len(prompt)))
                continue

            for c in prompt:
                alphabet.add(c)

            csv_f.write('%s,%d,%s\n' % (wavfn, wavlen, prompt))
            vocabulary.append(prompt)
            cnt += 1

    logging.info ("%s %d lines written." % (csv_fn, cnt) )

export_ds(ts_train, csv_train_fn)
export_ds(ts_test,  csv_test_fn)
export_ds(ts_test,  csv_dev_fn)

# export alphabet

alphabet_fn = '%s/alphabet.txt' % work_dir

with codecs.open(alphabet_fn, 'w', 'utf8') as alphabet_f:

    for c in sorted(alphabet):
        alphabet_f.write('%s\n' % c)
logging.info ("%s written." % alphabet_fn)

# export vocabulary

vocabulary_fn = '%s/vocabulary.txt' % work_dir

with codecs.open(vocabulary_fn, 'w', 'utf8') as vocabulary_f:

    for l in vocabulary:
        vocabulary_f.write('%s\n' % l)
logging.info ("%s written." % vocabulary_fn)

