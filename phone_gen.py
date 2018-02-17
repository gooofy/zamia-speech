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
# create new set of recordings from existing ones by adding
# phone codec effects
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

from optparse               import OptionParser

from nltools                import misc
from speech_transcripts     import Transcripts

PROC_TITLE      = 'phone_gen'

LANG            = 'de'
DEBUG_LIMIT     = 0
OUT_DIR         = 'tmp/phone_%s' % LANG # FIXME
FRAMERATE       = 16000
MIN_QUALITY     = 2

#
# init
#

misc.init_app(PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options])")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(lang=LANG)
logging.info("loading transcripts...done.")

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16_dir_%s" % LANG)

tmpfn_base  = '/tmp/tmp16_%08x' % os.getpid()
out_dir = OUT_DIR

#
# count good transcripts
#

total_good = 0
for ts in transcripts:

    if transcripts[ts]['quality']<MIN_QUALITY:
        continue
    cfn   = transcripts[ts]['cfn']
    if cfn.startswith('gsp'):
        continue
    if cfn.startswith('noisy'):
        continue
    total_good += 1

#
# main 
#

cnt = 1
for ts in transcripts:

    # print type(transcripts)

    if DEBUG_LIMIT:
        ts2 = random.choice(transcripts.keys())
        cfn   = transcripts[ts2]['cfn']
    else:
        cfn   = transcripts[ts]['cfn']

    if cfn.startswith('gsp'):
        continue
    if cfn.startswith('noisy'):
        continue
    cfn2 = 'phone'+cfn

    entry = transcripts[cfn]

    if entry['quality']<MIN_QUALITY:
        continue

    infn  = '%s/%s.wav' % (wav16_dir, cfn)
    outfn = '%s/%s.wav' % (out_dir, cfn2)

    if os.path.exists(outfn):
        continue

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

        # entry2 = { 'dirfn'   : entry['dirfn'],
        #            'audiofn' : entry['audiofn'],
        #            'prompt'  : entry['prompt'],
        #            'ts'      : ts2,
        #            'quality' : 2,
        #            'spk'     : entry['spk'],
        #            'cfn'     : cfn2 }

        # transcripts[cfn2] = entry2

    else:
        logging.error ('%s: wrong framerate %d' % (infn, fr))

    wav.close()

    cnt += 1

    if DEBUG_LIMIT>0 and cnt>DEBUG_LIMIT:
        break

transcripts.save()
logging.info ("new transcripts saved.")

