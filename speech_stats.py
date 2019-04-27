#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017, 2018, 2019 Guenter Bartsch
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
# print stats about an audio corpus
#

import sys
import re
import os
import StringIO
import ConfigParser
import wave
import codecs
import logging

from optparse           import OptionParser
from speech_transcripts import Transcripts
from speech_lexicon     import Lexicon
from nltools            import misc

PROC_TITLE = 'speech_stats'

DEBUG_LIMIT = 0
# DEBUG_LIMIT = 1000

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options] corpus")

parser.add_option ("-c", "--csv", dest="csvfn", type = "str",
                   help="CSV output file")
parser.add_option ("-s", "--speaker-stats", action="store_true", dest="speaker_stats", 
                   help="show per-speaker stats")
parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

(options, args) = parser.parse_args()

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

corpus_name   = args[0]
csv_fn        = options.csvfn
# csv_fn        = 'foo.csv'
speaker_stats = options.speaker_stats
# speaker_stats = True

# corpus_name = 'tedlium3'
# corpus_name = 'm_ailabs_en'
# corpus_name = 'voxforge_en'

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16")

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=corpus_name)
logging.info("loading transcripts...done.")

#
# compute stats
#

def format_duration(duration):
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)
    return "%3d:%02d:%02d" % (h, m, s)

spk_test = transcripts.spk_test

cnt              = 0
total_duration   = 0.0
duration_per_spk = {}
subs_per_spk     = {}
cnt              = 0
duration_per_set = {'train' : 0.0, 'test' : 0.0, 'poor' : 0.0, 'unrated' : 0.0}
subs_per_set     = {'train' : 0.0, 'test' : 0.0, 'poor' : 0.0, 'unrated' : 0.0}

for cfn in transcripts:

    entry = transcripts[cfn]
    spk = entry['spk']

    if entry['quality'] == 0:
        s = 'unrated'
    elif entry['quality'] == 1:
        s = 'poor'
    elif spk in spk_test:
        s = 'test'
    else:
        s = 'train'

    wavfn = '%s/%s/%s.wav' % (wav16_dir, corpus_name, cfn)
    wavef = wave.open(wavfn, 'rb')
    num_frames = wavef.getnframes()
    frame_rate = wavef.getframerate()
    duration = float(num_frames) / float(frame_rate)
    wavef.close()

    # print '%s has %d frames at %d samples/s -> %fs' % (wavfn, num_frames, frame_rate, duration)

    if not spk in duration_per_spk:
        duration_per_spk[spk] = 0.0
        subs_per_spk[spk]     = 0

    duration_per_set[s]   += duration
    subs_per_set[s]       += 1
    total_duration        += duration
    duration_per_spk[spk] += duration
    subs_per_spk[spk]     += 1

    cnt += 1

    if cnt % 1000 == 0:
       logging.info ('%6d/%6d: total=%s (train=%s, test=%s, poor=%s, unrated=%s)' % (cnt, len(transcripts), 
                                                                                     format_duration(total_duration),
                                                                                     format_duration(duration_per_set['train']),
                                                                                     format_duration(duration_per_set['test']),
                                                                                     format_duration(duration_per_set['poor']),
                                                                                     format_duration(duration_per_set['unrated'])))

    if DEBUG_LIMIT and cnt > DEBUG_LIMIT:
        logging.warn('debug limit reached -> stopping.')
        break


logging.info ('CORPUS STATS for %s: total=%s (train=%s, test=%s, poor=%s, unrated=%s)' % (corpus_name,  
                                                                             format_duration(total_duration),
                                                                             format_duration(duration_per_set['train']),
                                                                             format_duration(duration_per_set['test']),
                                                                             format_duration(duration_per_set['poor']),
                                                                             format_duration(duration_per_set['unrated'])))


# 
# CSV output
#

if csv_fn:
    with codecs.open(csv_fn, 'w', 'utf8') as csvf:
        csvf.write('speaker,duration,subs\n')
        for spk in sorted(duration_per_spk):
            csvf.write( "%s,%f,%d\n" % (spk, duration_per_spk[spk], subs_per_spk[spk]))
    logging.info('%s written.' % csv_fn)

#
# print stats per speaker if requested
#

if speaker_stats:
    logging.info('stats per speaker:')
    for spk in sorted(duration_per_spk):
        logging.info( "%-42s %s (%5d)" % (spk, format_duration(duration_per_spk[spk]), subs_per_spk[spk]))

