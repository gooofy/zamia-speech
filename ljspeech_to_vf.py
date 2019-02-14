#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2018 Guenter Bartsch
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
# convert LJSpeech corpus to a voxforge-like directory structure
# so we can import it using our regular tools
#
# WARNING: this is a very crude script, use with care!
#

import argparse
import os
import sys
import codecs
import re
import logging
import json

from optparse import OptionParser
from nltools  import misc

PROC_TITLE        = 'ljspeech_to_vf'
DEFAULT_NUM_CPUS  = 12

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-n", "--num-cpus", dest="num_cpus", type="int", default=DEFAULT_NUM_CPUS,
                   help="number of cpus to use in parallel, default: %d" % DEFAULT_NUM_CPUS)

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config('.speechrc')

speech_arc     = config.get("speech", "speech_arc")
speech_corpora = config.get("speech", "speech_corpora")

srcdir  = '%s/LJSpeech-1.1' % speech_arc
destdir = '%s/ljspeech' % speech_corpora

#
# audio, prompts
#

all_utts = set()

cnt = 0
with open('tmp/run_parallel.sh', 'w') as scriptf:

    folder = 'lindajohnson-11'
    dstdir = '%s/%s' % (destdir, folder)

    misc.mkdirs('%s/wav' % dstdir)
    misc.mkdirs('%s/etc' % dstdir)

    promptsfn = '%s/etc/prompts-original' % dstdir
    logging.debug ('dstdir: %s, promptsfn: %s' % (dstdir, promptsfn))

    with codecs.open ('%s/metadata.csv' % srcdir, 'r', 'utf8') as metaf:

        with codecs.open (promptsfn, 'w', 'utf8') as promptsf:

            for line in metaf:

                logging.debug(line)

                parts = line.strip().split('|')
                if len(parts) != 3:
                    logging.error('malformed line: %s' % line)
                    continue

                ts_orig = parts[2]
                uttid = parts[0].replace('_','-').lower()

                if uttid in all_utts:
                    logging.error('utterance id not unique:' % uttid)
                    continue
                all_utts.add(uttid)

                wav_in = '%s/wavs/%s.wav' % (srcdir, parts[0])

                wav_out = '%s/wav/%s.wav' % (dstdir, uttid)

                cmd = 'sox %s -r 16000 -b 16 -c 1 %s gain -n -1 compand 0.02,0.20 5:-60,-40,-10 -5 -90 0.1 ' % (wav_in, wav_out)
                logging.debug(cmd)
                # os.system(cmd)
                scriptf.write('echo %6d %s &\n' % (cnt, uttid))
                scriptf.write('%s &\n' % cmd)

                cnt += 1
                if (cnt % options.num_cpus) == 0:
                    scriptf.write('wait\n')

                promptsf.write(u'%s %s\n' % (uttid, ts_orig))

cmd = "bash tmp/run_parallel.sh"
print cmd
# os.system(cmd)
