#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2014, 2018 Guenter Bartsch
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

import sys
import os
import codecs
import traceback
import logging
import re
import wave

from optparse           import OptionParser
from time               import time
from nltools            import misc
from nltools.tokenizer  import tokenize
from kaldiasr.nnet3 import KaldiNNet3OnlineModel, KaldiNNet3OnlineDecoder

#
# - compute length stats about segments
# - compute set of words, print out words not covered by dict
# - decode segments using latest kaldi model
#

LANG        = 'de'
PROC_TITLE  = 'abook-analyze'

MODELDIR    = '../data/models/kaldi-chain-generic-%s-latest' % LANG
MODEL       = 'tdnn_sp'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# config
#

config = misc.load_config('.speechrc')

#
# command line
#

parser = OptionParser("usage: %prog [options] directory")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

subdirfn  = args[0]
wavdirfn  = '%s/wav' % subdirfn
promptsfn = '%s/etc/prompts-original' % subdirfn

#
# load prompts, compute audio stats
#

prompts = {}
words   = set()

prexp = re.compile(r"(\S+)\s(.*)$")

total_duration = 0.0

if os.path.isfile(promptsfn):
    with codecs.open(promptsfn, 'r', 'utf8') as promptsf:
        for line in promptsf:
            m = prexp.match(line.strip())
            if not m:
                # logging.error('failed to parse prompts line: %s' % repr(line))
                continue
            
            pid = m.group(1)
            prompt = m.group(2)

            if not prompt:
                continue

            prompts[pid] = prompt

            for word in tokenize(prompt, lang=LANG):
                words.add(word)

            wavfn = '%s/%s.wav' % (wavdirfn, pid)

            wavef = wave.open(wavfn, 'rb')

            num_frames = wavef.getnframes()
            frame_rate = wavef.getframerate()

            duration = float(num_frames) / float(frame_rate)

            # print '%s has %d frames at %d samples/s -> %fs' % (wavfn, num_frames, frame_rate, duration)

            total_duration += duration

logging.info("Total duration: %fs" % total_duration)

#
# dict
#

words_dict = set()

dictfn = '../data/src/dicts/dict-%s.ipa' % LANG

with open(dictfn, 'r') as f:

    while True:

        line = f.readline().rstrip().decode('utf8')

        if not line:
            break

        parts = line.split(';')

        k = parts[0]

        words_dict.add(k)

for word in sorted(words):
    if not word in words_dict:
        logging.warn(u"MISSING WORD: %s" % word)

#
# kaldi decoding
#

logging.info('kaldi: %s loading model from %s ...' % (MODEL, MODELDIR))
kaldi_model = KaldiNNet3OnlineModel (MODELDIR, MODEL, acoustic_scale=1.0, beam=7.0, frame_subsampling_factor=3)
decoder = KaldiNNet3OnlineDecoder (kaldi_model)

with codecs.open('reference.txt', 'w', 'utf8') as reff, \
     codecs.open('hypothesis.txt', 'w', 'utf8') as hypf:

    for pid in sorted(prompts):

        wavfn = '%s/%s.wav' % (wavdirfn, pid)

        if decoder.decode_wav_file(wavfn):
            s,l = decoder.get_decoded_string()
            logging.info("%s %s" % (pid, s))

            hypf.write(u"<s> %s </s> (%s)\n" % (s, pid))
            reff.write(u"<s> %s </s> (%s)\n" % (u" ".join(tokenize(prompts[pid], lang=LANG)), pid))

        else:
            logging.error('%s decoding did not work :(' % wavfn)

logging.info('reference.txt written.')
logging.info('hypothesis.txt written.')

#
# word-align
#

cmd = './word_align.pl reference.txt hypothesis.txt>%s.align' % subdirfn
logging.info(cmd)
os.system(cmd)


