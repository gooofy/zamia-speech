#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2017 Guenter Bartsch
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
# noise and echo effects
#
# these additional, artifically created recordings should help with
# noise resistance when used in training
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

PROC_TITLE      = 'noisy_gen'

LANG            = 'de'
DEBUG_LIMIT     = 0
OUT_DIR         = 'tmp/noisy_de' # FIXME
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
transcripts = Transcripts()
logging.info("loading transcripts...done.")

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16_dir_%s" % LANG)
noise_dir   = config.get("speech", "noise_dir")

bg_dir = '%s/bg' % noise_dir
fg_dir = '%s/fg/16kHz' % noise_dir
out_dir = OUT_DIR

#
# read fg file lengths
#

fg_lens = {}

for fgfn in os.listdir(fg_dir):

    wav = wave.open('%s/%s' % (fg_dir, fgfn), 'r')

    fr = wav.getframerate()
    if fr == FRAMERATE:
        fg_lens[fgfn] = float(wav.getnframes()) / float(FRAMERATE)
    else:
        logging.error('%s: wrong framerate %d' % (fgfn, fr))

    wav.close()

#
# read bg file lengths
#

bg_lens = {}

cnt = 0

for bgfn in os.listdir(bg_dir):

    if not bgfn.endswith('_16k.wav'):
        continue

    # print bgfn

    wav = wave.open('%s/%s' % (bg_dir, bgfn), 'r')

    fr = wav.getframerate()
    if fr == FRAMERATE:
        bg_lens[bgfn] = float(wav.getnframes()) / float(FRAMERATE)
    else:
        logging.error('%s: wrong framerate %d' % (bgfn, fr))

    wav.close()

# print repr(bg_lens)

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

for ts in transcripts:

    # print type(transcripts)

    if DEBUG_LIMIT:
        ts2 = random.choice(transcripts.keys())
        cfn   = transcripts[ts2]['cfn']
    else:
        cfn   = transcripts[ts]['cfn']

    if cfn.startswith('gsp'):
        continue
    cfn2 = 'noisy'+cfn

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

        in_len = float(wav.getnframes()) / float(FRAMERATE)
        fg_level = random.uniform (-1.0, 0.0)

        logging.info ('%5d/%5d %6.2fs lvl=%2.3f %s' % (cnt, total_good, in_len, fg_level, cfn))

        logging.debug ('    entry: %s' % repr(entry))

        #
        # forground noises
        #

        fgfn_1 = random.choice(fg_lens.keys())
        fgfn_2 = random.choice(fg_lens.keys())

        fg_len = fg_lens[fgfn_1] + fg_lens[fgfn_2] + in_len

        logging.debug ('   fg: len=%6.2fs fn1=%s fn2=%s' % (fg_len, fgfn_1, fgfn_2))

        ts2 = 'nspc ' + entry['ts'] + ' nspc'
        logging.debug ('   ts2: %s' % ts2)

        #
        # background noise
        #

        bgfn = None
        while not bgfn:
            
            bgfn2 = random.choice(bg_lens.keys())
            bgl = bg_lens[bgfn2]
            if bgl > fg_len:
                bgfn = bgfn2
                bg_off = random.uniform (0, bgl - fg_len)

        bg_level = random.uniform (-15.0, -10.0)

        logging.debug ('   bg: off=%6.2fs fn=%s' % (bg_off, bgfn))

        # reverb [-w|--wet-only] [reverberance (50%) [HF-damping (50%)
        #        [room-scale (100%) [stereo-depth (100%)
        #        [pre-delay (0ms) [wet-gain (0dB)]]]]]]

        reverb_level = random.uniform(0.0, 50.0)

        # compand attack1,decay1{,attack2,decay2}
        #        [soft-knee-dB:]in-dB1[,out-dB1]{,in-dB2,out-dB2}
        #        [gain [initial-volume-dB [delay]]]


        cmd = 'sox -m "|sox --norm=%f %s/%s %s %s/%s -p compand 0.01,0.2 -90,-10 -5 reverb %f" "|sox --norm=%f %s/%s -p trim %f %f" %s' % \
              (fg_level, fg_dir, fgfn_1, infn, fg_dir, fgfn_2, reverb_level, bg_level, bg_dir, bgfn, bg_off, fg_len, outfn)

        logging.debug('   cmd: %s' % cmd)

        os.system(cmd)

        entry2 = { 'dirfn'   : entry['dirfn'],
                   'audiofn' : entry['audiofn'],
                   'prompt'  : entry['prompt'],
                   'ts'      : ts2,
                   'quality' : 2,
                   'spk'     : entry['spk'],
                   'cfn'     : cfn2 }

        transcripts[cfn2] = entry2

    else:
        logging.error ('%s: wrong framerate %d' % (infn, fr))

    wav.close()

    cnt += 1

    if DEBUG_LIMIT>0 and cnt>DEBUG_LIMIT:
        break

transcripts.save()
logging.info ("new transcripts saved.")

