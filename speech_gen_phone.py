#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2017, 2018 Guenter Bartsch
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
# create corpus from an existing one by adding phone codec effects to the
# recordings
#
# these additional, artifically created recordings should improve
# model performance for (8kHz) phone recordings
#

import os
import sys
import logging
import traceback
import locale
import codecs
import wave
import random
import copy

from optparse               import OptionParser

from nltools                import misc
from speech_transcripts     import Transcripts

PROC_TITLE      = 'speech_gen_phone'

DEBUG_LIMIT     = 0
FRAMERATE       = 16000
MIN_QUALITY     = 2
SKIP            = 4 # only generate phone-variant of every 4th existing entry

#
# init
#

misc.init_app(PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options] corpus")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

corpus_in  = args[0]
corpus_out = corpus_in + '_phone'

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=corpus_in)
logging.info("loading transcripts...done.")

#
# config
#

config = misc.load_config('.speechrc')

corpora     = config.get("speech", "speech_corpora")
wav16_dir   = config.get("speech", "wav16")

out_dir     = '%s/%s' % (corpora, corpus_out)
tmpfn_base  = '/tmp/tmp16_%08x' % os.getpid()

if os.path.exists(out_dir):
    logging.error("%s already exists!" % out_dir)
    sys.exit(1)

logging.info ("creating %s ..." % out_dir)
misc.mkdirs(out_dir)

#
# count good transcripts
#

total_good = 0
for ts in transcripts:

    if transcripts[ts]['quality']<MIN_QUALITY:
        continue
    total_good += 1

#
# main 
#

cnt = 1
random.seed(42)

for ts in transcripts:

    # print type(transcripts)

    if DEBUG_LIMIT:
        ts2 = random.choice(transcripts.keys())
        cfn   = transcripts[ts2]['cfn']
    else:
        cfn   = transcripts[ts]['cfn']

    entry = transcripts[cfn]

    if entry['quality']<MIN_QUALITY:
        continue

    if cnt % SKIP == 0:

        infn     = '%s/%s/%s.wav' % (wav16_dir, corpus_in, cfn)
        pkgdirfn = '%s/%s' % (out_dir, entry['dirfn'])
        audiofn2 = entry['audiofn'] + '-phone'

        if not os.path.exists(pkgdirfn):
            misc.mkdirs('%s/etc' % pkgdirfn)
            misc.mkdirs('%s/wav' % pkgdirfn)

        outfn = '%s/wav/%s.wav' % (pkgdirfn, audiofn2)

        wav = wave.open(infn, 'r')

        fr = wav.getframerate()
        if fr == FRAMERATE:

            op = random.choice(['8kHz', 'lpc ', 'gsm '])

            logging.info ('%5d/%5d %s %s' % (cnt, total_good, op, cfn))

            if op == '8kHz':
                tmpfn = '%s.wav' % tmpfn_base

            elif op == 'lpc ':
                tmpfn = '%s.lpc' % tmpfn_base
            
            else:
                tmpfn = '%s.gsm' % tmpfn_base

            cmd = 'sox %s -r 8000 -c 1 %s' % (infn, tmpfn)
            logging.debug('   cmd: %s' % cmd)
            os.system(cmd)

            cmd = 'sox %s -b 16 -r 16000 -c 1 %s' % (tmpfn, outfn)
            logging.debug('   cmd: %s' % cmd)
            os.system(cmd)


            promptfn = '%s/etc/prompts-original' % pkgdirfn

            with codecs.open(promptfn, 'a', 'utf8') as promptf:
                promptf.write('%s %s\n' % (audiofn2, entry['ts']))

        else:
            logging.error ('%s: wrong framerate %d' % (infn, fr))

        wav.close()

    cnt += 1

    if DEBUG_LIMIT>0 and cnt>DEBUG_LIMIT:
        break

