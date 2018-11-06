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
# use kaldi to decode so far not reviewed submissions, auto-accept those
# that decode to their prompt correctly
#

import os
import sys
import logging
import readline
import atexit
import traceback

from time               import time
from optparse           import OptionParser
from StringIO           import StringIO

from nltools            import misc
from nltools.phonetics  import ipa2xsampa
from nltools.tokenizer  import tokenize

from speech_lexicon     import Lexicon
from speech_transcripts import Transcripts

from kaldiasr.nnet3     import KaldiNNet3OnlineModel, KaldiNNet3OnlineDecoder

DEFAULT_ASR_MODEL = 'kaldi-chain-voxforge-de-latest'

MODELDIR    = 'data/models/%s'
SAVE_RATE   = 10
FAILLOG     = 'tmp/decoding_fails.txt'

#
# init 
#

misc.init_app ('auto_review')

config = misc.load_config ('.speechrc')

#
# command line
#

parser = OptionParser("usage: %prog [options] corpus")

parser.add_option ("-a", "--all", action="store_true", dest="do_all", 
                   help="do not use ASR but auto-rate all matching submissions")

parser.add_option ("-f", "--filter", dest="ts_filter", type = "str", 
                   help="filter (default: no filtering)")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default="de",
                   help="tokenizer language (default: de)")

parser.add_option ("-m", "--asr-model", dest="asr_model", type = "str", default=DEFAULT_ASR_MODEL,
                   help="kaldi asr model to use (default: %s)" % DEFAULT_ASR_MODEL)

parser.add_option ("-R", "--result-file", dest="outfn", type = "str", default='review-result.csv',
                   help="result file (default: review-result.csv)")

parser.add_option ("-r", "--rating", dest="rating", type="int", default=2,
                   help="rating to apply (1=Poor 2=Fair 3=Good), default: 2 (fair)")

#
# offset and step are meant for multi-processor operation:
# start one review process per CPU, offsetting them properly, e.g. on a 4 CPU system:
#
# auto_review -s 4 -o 0 &
# auto_review -s 4 -o 1 &
# auto_review -s 4 -o 2 &
# auto_review -s 4 -o 3 &
#

parser.add_option ("-s", "--step", dest="step", type="int", default=1,
                   help="transcript step (default: 1")

parser.add_option ("-o", "--offset", dest="offset", type="int", default=0,
                   help="transcript offset to start from (default: 0")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

(options, args) = parser.parse_args()

ts_filter = options.ts_filter.decode('utf8') if options.ts_filter else None

if len(args)!=1:
    parser.print_usage()
    sys.exit(1)

corpus = args[0]

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

wav16_dir   = config.get("speech", "wav16")

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=corpus)
logging.info("loading transcripts...done.")

#
# load kaldi model
#

if not options.do_all:
    logging.info("loading kaldi model...")
    kaldi_model = KaldiNNet3OnlineModel (MODELDIR % options.asr_model, acoustic_scale=1.0, beam=7.0, frame_subsampling_factor=3)
    logging.info("loading kaldi model...done.")

#
# main
#

num_rated  = 0
idx        = 0
next_idx   = options.offset
num_failed = 0
if not options.do_all:
    decoder   = KaldiNNet3OnlineDecoder (kaldi_model)

with open (options.outfn, 'w') as outf:

    for utt_id in transcripts:

        ts = transcripts[utt_id]

        if ts['quality'] != 0:
            continue

        if ts_filter and not (ts_filter in utt_id):
            continue

        idx += 1
        if idx != next_idx + 1:
            continue

        next_idx += options.step

        wavfn = '%s/%s/%s.wav' % (wav16_dir, corpus, utt_id)

        prompt = ' '.join(tokenize(ts['prompt'], lang=options.lang))

        if not prompt:
            logging.info("%7d, # rated: %5d %-20s no prompt." % (idx, num_rated, utt_id))
            continue

        if options.do_all:

            logging.info("%7d, # rated: %5d %-20s manual rating: %d" % (idx, num_rated, utt_id, options.rating))
    
            outf.write ('%s;%d\n' % (utt_id, options.rating))

            num_rated += 1
    
        else:    

            try:

                if decoder.decode_wav_file(wavfn):

                    s, l = decoder.get_decoded_string()

                    hyp = ' '.join(tokenize(s, lang=options.lang))

                    if hyp == prompt:
                        logging.info("%7d, # rated: %5d %-20s *** MATCH ***" % (idx, num_rated, utt_id))
                        outf.write ('%s;%d\n' % (utt_id, options.rating))
                        outf.flush()
                        logging.debug ('    %s written.' % options.outfn)
                        num_rated += 1
                    else:
                        logging.info("%7d, # rated: %5d %-20s no match" % (idx, num_rated, utt_id))
                        logging.debug("    hyp   : %s" % repr(hyp))
                        logging.debug("    prompt: %s" % repr(prompt))
                        
                else:
                    logging.info("%7d, # rated: %5d %-20s decoder failed" % (idx, num_rated, utt_id))

            except:
                logging.error('EXCEPTION CAUGHT WHILE DECODING %s\n %s' % (wavfn, traceback.format_exc()))
                with open(FAILLOG, 'a') as faillog:
                    faillog.write('%s\n' % wavfn)
                num_failed += 1

logging.info ("%s written." % options.outfn)

if num_failed:
    logging.warn ("logged %d files where decoding failed to: %s" % (num_failed, FAILLOG))


