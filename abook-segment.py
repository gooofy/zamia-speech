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
import datetime
import logging
import wave, struct, array

import numpy as np

from optparse           import OptionParser
from nltools            import misc

#
# - segment according to silence measurements
#

SAMPLE_RATE                = 16000

DEFAULT_MIN_UTT_LENGTH     = 2   # seconds
DEFAULT_MAX_UTT_LENGTH     = 9   # seconds
DEFAULT_SILENCE_LEVEL      = 2048
DEFAULT_MIN_SIL_LENGTH     = 0.07 # seconds

DEFAULT_OUT_DIR            = 'abook/segments'

# debug purposes only, set to 0 to disable debug limit
# DEBUG_LENGTH       = 3960000
DEBUG_LENGTH       = 0

PROC_TITLE = 'abook-segment'

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

parser = OptionParser("usage: %prog [options] foo.wav")

parser.add_option("-s", "--silence-level", dest="silence_level", type = "int", default=DEFAULT_SILENCE_LEVEL,
                   help="silence level (default: %d / 65536)" % DEFAULT_SILENCE_LEVEL)
parser.add_option("-l", "--min-sil-length", dest="min_sil_length", type = "float", default=DEFAULT_MIN_SIL_LENGTH,
                   help="minimum silence length (default: %5.2fs)" % DEFAULT_MIN_SIL_LENGTH)
parser.add_option("-m", "--min-utt-length", dest="min_utt_length", type = "float", default=DEFAULT_MIN_UTT_LENGTH,
                   help="minimum utterance length (default: %5.2fs)" % DEFAULT_MIN_UTT_LENGTH)
parser.add_option("-M", "--max-utt-length", dest="max_utt_length", type = "float", default=DEFAULT_MAX_UTT_LENGTH,
                   help="maximum utterance length (default: %5.2fs)" % DEFAULT_MAX_UTT_LENGTH)
parser.add_option("-o", "--out-dir", dest="outdirfn", type = "str", default=DEFAULT_OUT_DIR,
                   help="output directory (default: %s)" % DEFAULT_OUT_DIR)
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

inputfn        = args[0]
outdirfn       = options.outdirfn
min_utt_length = options.min_utt_length 
max_utt_length = options.max_utt_length 
min_sil_length = options.min_sil_length 
silence_level  = options.silence_level

#
# output dir
#

if os.path.isdir(outdirfn):
    logging.error ('%s already exists!' % outdirfn)
    sys.exit(1)

os.mkdir(outdirfn)

#
# read all samples into memory so we have random access to them
# when we're looking for cut-points
#

wavf = wave.open(inputfn, 'r')
length = wavf.getnframes()
sr     = wavf.getframerate()

logging.info ('reading %s (%d samples, %d samples/s)...' % (inputfn, length, sr))

if sr != SAMPLE_RATE:
    logging.error ('%s: expected sample rate: %d, found:%d' % (inputfn, SAMPLE_RATE, sr))
    sys.exit(2)

if DEBUG_LENGTH>0 and length >DEBUG_LENGTH:
    length = DEBUG_LENGTH

wd = wavf.readframes(length)
samples = np.fromstring(wd, dtype=np.int16)

#
# silence detection
#

logging.info('silence detection...')

offset        = 0
silence_start = None
silences      = []

while offset < length:

    if abs(samples[offset]) <= silence_level:
        if not silence_start:
            silence_start = offset

    else:
        if silence_start:
            sil_len = offset-silence_start
            if sil_len > min_sil_length * SAMPLE_RATE:
                silences.append((silence_start, sil_len))
            silence_start = None    

    offset += 1

    if offset % 960000 == 0:
        logging.info ('silence detection... %5.1f%% done' % (offset * 100.0 / length))

logging.info('silence detection done, detected %d potential cut points.' % len(silences))

#
# split segments until they are short enough
#

segments_todo = [ (0, length-1) ]
segments_done = []

while segments_todo:

    s_start, s_end = segments_todo.pop()

    if (s_end - s_start) < (max_utt_length * SAMPLE_RATE):
        logging.debug ('segment done: %7d to %7d (%5.1fs)' % (s_start, s_end, float(s_end-s_start) / SAMPLE_RATE))
        segments_done.append((s_start, s_end))
        continue

    # look for best cut point, if any

    cut_start = s_start + min_utt_length * SAMPLE_RATE
    cut_end   = s_end   - min_utt_length * SAMPLE_RATE

    best_cut     = None
    best_cut_len = None

    for sil_start, sil_len in silences:

        if sil_start < cut_start or sil_start > cut_end:
            continue

        if not best_cut_len or sil_len > best_cut_len:
            best_cut     = sil_start
            best_cut_len = sil_len

    if not best_cut:
        logging.debug ('no cut point found between %d and %d' % (cut_start, cut_end))
        segments_done.append((s_start, s_end))
    else:

        segments_todo.append((s_start, best_cut + best_cut_len/2))
        segments_todo.append((best_cut + best_cut_len/2 + 1, s_end))
        logging.debug ('best cut point between %d and %d: %d (len: %d)' % (cut_start, cut_end, best_cut, best_cut_len))

#
# sort segments
#

segments_sorted = sorted(segments_done, key=lambda tup: tup[0])

#
# write out segments wav files
#

wavoutcnt  = 0
for s_start, s_end in segments_sorted:

    cur_buffer = []
    for s in samples[s_start:s_end]:
        cur_buffer.append(s)

    wavoutfn  = "%s/segment_%04d.wav" % (outdirfn, wavoutcnt)

    wavoutf   = wave.open(wavoutfn, 'w')
    wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))

    A = array.array('h', cur_buffer)
    wd = A.tostring()
    wavoutf.writeframes(wd)
    wavoutf.close()
    wavoutcnt += 1

    seconds = float(len(cur_buffer)) / float(SAMPLE_RATE)
    logging.info ('segment [%7d:%7d] %s written, %5.1fs.' % (s_start, s_end, wavoutfn, seconds))
   
# #
# # write out silences (for debug purposes)
# #
# 
# wavoutcnt  = 0
# for s_start, s_len in silences:
# 
#     s_end = s_start + s_len
# 
#     cur_buffer = []
#     for s in samples[s_start:s_end]:
#         cur_buffer.append(s)
# 
#     wavoutfn  = "%s/sil_%04d.wav" % (outdirfn, wavoutcnt)
# 
#     wavoutf   = wave.open(wavoutfn, 'w')
#     wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
# 
#     A = array.array('h', cur_buffer)
#     wd = A.tostring()
#     wavoutf.writeframes(wd)
#     wavoutf.close()
#     wavoutcnt += 1
# 
#     seconds = float(len(cur_buffer)) / float(SAMPLE_RATE)
#     logging.info ('silence [%7d:%7d] %s written, %5.1fs.' % (s_start, s_end, wavoutfn, seconds))
   


 
sys.exit(0)

# print "Reading %6d/%6d samples from %s..." % (len(samples), length, tmpwav16fn),

i          = 0
offset     = 0
cur_buffer = []
wavoutcnt  = 0

while offset < length:

    wd = wavf.readframes(FRAMES_PER_BUFFER)
    i += 1
    offset = i * FRAMES_PER_BUFFER

    try:

        samples = np.fromstring(wd, dtype=np.int16)

        audio, finalize = vad.process_audio(samples)

        # logging.info ('len(cur_buffer)=%5d finalize: %s' % (len(cur_buffer), finalize))

        # logging.info ('audio: %s' % audio)
        # import pdb; pdb.set_trace()

        if audio:
            cur_buffer.extend(audio)

        if finalize:

            wavoutfn  = "%s/seg-%04d.wav" % (outdirfn, wavoutcnt)

            wavoutf   = wave.open(wavoutfn, 'w')
            wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))

            A = array.array('h', cur_buffer)
            wd = A.tostring()
            wavoutf.writeframes(wd)
            wavoutf.close()
            wavoutcnt += 1

            seconds = float(len(cur_buffer)) / float(SAMPLE_RATE)
            logging.info ('%5.1f%% segment %s written, %5.1fs.' % (offset * 100.0 / length, wavoutfn, seconds))

            cur_buffer = []

    except:
        logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

logging.info ('Done %d of %d.' % (offset, length))

#
# cleanup
#

os.system ('rm %s' % tmpwav16fn)

