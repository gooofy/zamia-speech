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
# retrieve segmentation results from kaldi, produce voxforge
# directory structure containing prompts and wavs
#

import os
import sys
import logging
import traceback
import codecs
import wave, struct, array

import numpy as np

from optparse import OptionParser

from nltools                import misc

WORKDIR          = 'data/dst/asr-models/kaldi/segmentation'

SAMPLE_RATE      = 16000

#
# init 
#

misc.init_app ('abook-kaldi-retrieve')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] srcdir")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

srcdirfn = args[0]

#
# read wavs
#

wavdict = {}

for fn in os.listdir(srcdirfn):

    if not fn.endswith('.wav'):
        continue

    wavfn = '%s/%s' % (srcdirfn, fn)
    wav_id = os.path.splitext(fn)[0]

    wavf = wave.open(wavfn, 'r')
    length = wavf.getnframes()
    sr     = wavf.getframerate()

    logging.info ('reading %s (%d samples, %d samples/s, %fs)...' % (fn, length, sr, float(length)/float(sr)))

    if sr != SAMPLE_RATE:
        logging.error ('%s: expected sample rate: %d, found:%d' % (inputfn, SAMPLE_RATE, sr))
        sys.exit(2)

    wd = wavf.readframes(length)
    samples = np.fromstring(wd, dtype=np.int16)

    wavdict[wav_id] = samples

#
# read prompts
#

promptsdict = {}

promptfn = '%s/data/segmentation_result_a_cleaned_b/text' % WORKDIR

with codecs.open(promptfn, 'r', 'utf8') as promptf:

    for line in promptf:
        parts = line.strip().split(u" ")

        promptsdict[parts[0]] = u" ".join(parts[1:])

logging.info ('read %s : %d segments.' % (promptfn, len(promptsdict)))

#
# extract segments
#

segmentsfn = '%s/data/segmentation_result_a_cleaned_b/segments' % WORKDIR

segcnt = 0

with codecs.open(segmentsfn, 'r', 'utf8') as segmentsf:

    for line in segmentsf:
        parts = line.strip().split(u" ")

        if len(parts) != 4:
            logging.error ('%s: failed to parse line: %s' % (segmentsfn, line))

        seg_id     = parts[0]
        wavfn      = parts[1]
        wav_id     = os.path.basename(wavfn)
        seg_start  = float(parts[2])
        seg_end    = float(parts[3])

        #
        # create output dir structure if it doesn't exist
        #

        outdirfn = 'abook/out/%s' % os.path.basename(wav_id)

        if not os.path.exists(outdirfn):
            logging.info ('creating %s ...' % outdirfn)
            misc.mkdirs(outdirfn)
            misc.mkdirs('%s/etc' % outdirfn)
            misc.mkdirs('%s/wav' % outdirfn)

        #
        # prompt
        #

        uid = 'de5-%06d' % segcnt
        segcnt += 1

        prompt    = promptsdict[seg_id]
        promptsfn = '%s/etc/prompts-original' % outdirfn
        with codecs.open (promptsfn, 'a', 'utf8') as promptsf:
            promptsf.write(u'%s %s\n' % (uid, prompt))


        #
        # create wave file
        #

        s_start = int(seg_start * SAMPLE_RATE)
        s_end   = int(seg_end * SAMPLE_RATE)

        segment_samples = []
        for s in wavdict[wav_id][s_start:s_end]:
            segment_samples.append(s)

        wavoutfn  = "%s/wav/%s.wav" % (outdirfn, uid)

        wavoutf   = wave.open(wavoutfn, 'w')
        wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))

        A = array.array('h', segment_samples)
        wd = A.tostring()
        wavoutf.writeframes(wd)
        wavoutf.close()

        seconds = float(len(segment_samples)) / float(SAMPLE_RATE)
        logging.info ('segment [%7d:%7d] %s written, %5.1fs.' % (s_start, s_end, wavoutfn, seconds))

