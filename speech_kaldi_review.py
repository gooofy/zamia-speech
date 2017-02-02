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
# use kaldi to decode so far not reviewed submissions, auto-accept those
# that decode to their prompt correctly
#

import os
import sys
import logging
import readline
import atexit
import traceback
from time import time
from optparse import OptionParser
from StringIO import StringIO
import utils
from speech_lexicon import ipa2xsampa, Lexicon
from speech_transcripts import Transcripts

from gmm_decode import GMMDecoder

MODELDIR    = 'data/kaldi-voxforge-de-r20160922/'
MODEL       = 'tri2b_mmi_b0.05'
WORKDIR     = 'tmp'

logging.basicConfig(level=logging.DEBUG)

#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

#
# config
#

config = utils.load_config()

kaldi_root  = config.get("speech", "kaldi_root")
wav16_dir   = config.get("speech", "wav16_dir_de")

#
# load lexicon, transcripts
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

print "loading transcripts..."
transcripts = Transcripts()

#
# kaldi decoder
#

decoder = GMMDecoder(MODELDIR, MODEL, WORKDIR)

#
# main
#

num_correct = 0
for utt_id in transcripts:

    ts = transcripts[utt_id]

    if ts['quality'] != 0:
        continue

    wavfn = '%s/%s.wav\n' % (wav16_dir, utt_id)

    prompt = ts['prompt'].lower()

    time_start = time()
    if decoder.decode(wavfn):
        print
        print 'decoding worked!'

        s = decoder.get_decoded_string().strip()

        print "decoded: >%s< (likelihood: %f)" % (s, decoder.get_likelihood())
        print "prompt : >%s< " % (prompt)

        if s == prompt:
            print "*************** CORRECT! ****************"
            num_correct += 1
            print "%d correct files so far."

    else:
        print
        print '%s decoding did not work :(' % utt_id

    print "decoding took %8.2fs" % ( time() - time_start )
    print


