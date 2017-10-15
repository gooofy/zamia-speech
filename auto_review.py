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

from nltools            import misc
from nltools.phonetics  import ipa2xsampa
from nltools.tokenizer  import tokenize

from speech_lexicon     import Lexicon
from speech_transcripts import Transcripts

from kaldisimple.nnet3  import KaldiNNet3OnlineModel, KaldiNNet3OnlineDecoder

MODELDIR    = 'data/models/kaldi-nnet3-voxforge-%s-latest'
MODEL       = 'nnet_tdnn_a' 
SAVE_RATE   = 10

#
# init 
#

misc.init_app ('auto_review')

config = misc.load_config ('.speechrc')

#
# command line
#

parser = OptionParser("usage: %prog [options] [filter])")

parser.add_option("-a", "--all", action="store_true", dest="do_all", 
                  help="do not use ASR but auto-rate all matching submissions")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                  help="language (default: de)")

parser.add_option("-r", "--rating", dest="rating", type="int", default=2,
                  help="rating to apply (1=Poor 2=Fair 3=Good), default: 2 (fair)")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

ts_filter = None

if len(args)==1:
    ts_filter = args[0].decode('utf8')

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

wav16_dir   = config.get("speech", "wav16_dir_%s" % options.lang)

#
# load lexicon, transcripts
#

logging.info("loading lexicon...")
lex = Lexicon(lang=options.lang)
logging.info("loading lexicon...done.")

logging.info("loading transcripts...")
transcripts = Transcripts(lang=options.lang)
logging.info("loading transcripts...done.")

#
# load kaldi model
#

if not options.do_all:
    logging.info("loading kaldi model...")
    kaldi_model = KaldiNNet3OnlineModel (MODELDIR % options.lang, MODEL)
    logging.info("loading kaldi model...done.")

#
# main
#

num_rated = 0
cnt       = 0
decoder   = KaldiNNet3OnlineDecoder (kaldi_model)

for utt_id in transcripts:

    ts = transcripts[utt_id]

    if ts['quality'] != 0:
        continue

    if ts_filter and not (ts_filter in utt_id):
        continue

    cnt += 1

    wavfn = '%s/%s.wav' % (wav16_dir, utt_id)

    prompt = ' '.join(tokenize(ts['prompt']))

    print "%7d, # rated: %5d %s" % (cnt, num_rated, wavfn)

    if not options.do_all:
        if decoder.decode_wav_file(wavfn):

            s, l = decoder.get_decoded_string()

            hyp = ' '.join(tokenize(s))

            print
            print "*****************************************************************"
            print "**", wavfn
            print "**", hyp
            print "**", prompt
            print "**"
            if hyp == prompt:
                print "** ++++++++++++++ MATCH ++++++++++++++"
            else:
                print "**              MISMATCH              "
                
            print "**"
            print "*****************************************************************"
            print
            if hyp != prompt:
                continue

        else:
            print 'decoding did not work :('
            continue

    ts['ts']      = prompt
    ts['quality'] = options.rating

    num_rated += 1
    
    if num_rated % SAVE_RATE == 0:
        logging.info("saving transcripts...")
        transcripts.save()
        logging.info("saving transcripts...done.")

logging.info("saving transcripts...")
transcripts.save()
logging.info("saving transcripts...done.")

