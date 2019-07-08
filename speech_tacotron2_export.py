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
# generate filelists for tacotron-2 training
#
# https://github.com/NVIDIA/tacotron2
#


import sys
import os
import ConfigParser
import codecs
import logging

from optparse           import OptionParser
from nltools            import misc
from speech_transcripts import Transcripts

DEBUG_LIMIT  = 0
# DEBUG_LIMIT = 4096
# DEBUG_LIMIT = 512

PROC_TITLE      = 'speech_tacotron2_export'
MIN_QUALITY     = 2

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# config
#

config = misc.load_config('.speechrc')

speech_corpora_dir = config.get("speech", "speech_corpora")
wav16_dir          = config.get("speech", "wav16")

#
# command line
#

speech_corpora_available = []
for corpus in os.listdir(speech_corpora_dir):
    if not os.path.isdir('%s/%s' % (speech_corpora_dir, corpus)):
        continue
    speech_corpora_available.append(corpus)

parser = OptionParser("usage: %%prog [options] <corpus> <speaker>\n  corporus: one of %s" % ", ".join(speech_corpora_available))

parser.add_option ("-l", "--lang", dest="lang", type = "str", default="de",
                   help="language (default: de)")

parser.add_option ("-o", "--output-dir", dest="output_dir", type = "str", default="filelists",
                   help="output directory (default: filelists)")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 2:
    parser.print_help()
    sys.exit(0)

corpus_name  = args[0]
speaker      = args[1]
lang         = options.lang

misc.mkdirs(options.output_dir)

#
# main
#

logging.info ('reading transcripts from %s ...' % corpus_name)

transcripts = Transcripts(corpus_name=corpus_name)

trainfn = '%s/%s_train_filelist.txt' % (options.output_dir, speaker)
valfn   = '%s/%s_val_filelist.txt' % (options.output_dir, speaker)

with codecs.open(valfn, 'w', 'utf8') as valf:
    with codecs.open(trainfn, 'w', 'utf8') as trainf:

        cnt = 0
        for cfn in transcripts:

            ts = transcripts[cfn]

            if ts['quality'] < MIN_QUALITY:
                continue

            if ts['spk'] != speaker:
                # logging.debug(ts['spk'])
                continue

            ts_orig  = ts['ts']

            wavfn = '%s/%s/%s.wav' % (wav16_dir, corpus_name, cfn)
            
            if cnt % 100 == 0:
                logging.info('%7d / %7d %-30s %s' % (cnt, len(transcripts), wavfn, ts_orig[:80]))

            if cnt % 20 == 0:
                valf.write('%s|%s\n' % (wavfn, ts_orig))
            else:
                trainf.write('%s|%s\n' % (wavfn, ts_orig))

            cnt += 1
            if DEBUG_LIMIT and cnt >= DEBUG_LIMIT:
                logging.warn ('DEBUG LIMIT REACHED.')
                break

logging.info('%s written.' % trainfn)
logging.info('%s written.' % valfn)

