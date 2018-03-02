#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017 Guenter Bartsch
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
# print stats about audio, dictionary and models
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

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options])")

parser.add_option ("-c", "--csv", dest="csvfn", type = "str",
                   help="CSV output file")
parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16_dir_%s" % options.lang)

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(lang=options.lang)
logging.info("loading transcripts...done.")

#
# load lexicon
#

logging.info("loading lexicon...")
lex = Lexicon(lang=options.lang)
logging.info("loading lexicon...done.")

#
# lexicon stats
#

logging.info("%d lexicon entries." % len(lex))

#
# audio stats
#

def format_duration(duration):
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)
    return "%3d:%02d:%02d" % (h, m, s)

logging.info ('calculating audio duration...')

total_duration   = 0.0
duration_per_spk = {}
subs_per_spk     = {}
cnt              = 0

for cfn in transcripts:

    quality = transcripts[cfn]['quality']
    if quality < 2:
        continue

    wavfn = '%s/%s.wav' % (wav16_dir, cfn)

    wavef = wave.open(wavfn, 'rb')

    num_frames = wavef.getnframes()
    frame_rate = wavef.getframerate()

    duration = float(num_frames) / float(frame_rate)

    # print '%s has %d frames at %d samples/s -> %fs' % (wavfn, num_frames, frame_rate, duration)

    total_duration += duration

    spk = transcripts[cfn]['spk']

    if not spk in duration_per_spk:
        duration_per_spk[spk] = 0.0
        subs_per_spk[spk]     = 0

    duration_per_spk[spk] += duration
    subs_per_spk[spk]     += 1

    wavef.close()

    cnt += 1

    if cnt % 1000 == 0:
       logging.info ('%6d/%6d: duration=%s' % (cnt, len(transcripts), format_duration(total_duration)))


logging.info( "total duration of all good submissions: %s" % format_duration(total_duration))
logging.info( "good submissions per user:")
for spk in sorted(duration_per_spk):
    logging.info( "%-42s %s (%3d)" % (spk, format_duration(duration_per_spk[spk]), subs_per_spk[spk]))

if options.csvfn:
    with codecs.open(options.csvfn, 'w', 'utf8') as csvf:
        csvf.write('speaker,duration,subs\n')
        for spk in sorted(duration_per_spk):
            csvf.write( "%s,%f,%d\n" % (spk, duration_per_spk[spk], subs_per_spk[spk]))
    logging.info('%s written.' % options.csvfn)


#
# sphinx model stats
#

with codecs.open('data/dst/speech/%s/cmusphinx_cont/logs/sphinxtrain_run.log' % options.lang, 'r', 'utf8') as logf:
    for line in logf:
        if 'WORD ERROR RATE' in line:
            logging.info( "cmusphinx cont model: %s" % line.strip())

with codecs.open('data/dst/speech/%s/cmusphinx_ptm/logs/sphinxtrain_run.log' % options.lang, 'r', 'utf8') as logf:
    for line in logf:
        if 'WORD ERROR RATE' in line:
            logging.info( "cmusphinx ptm model: %s" % line.strip())

#
# kaldi model stats
#

logging.info( "kaldi models: ")
with codecs.open('data/dst/speech/%s/kaldi/RESULTS.txt' % options.lang, 'r', 'utf8') as logf:
    for line in logf:
        logging.info( line.strip())

#
# sequitur model stats
#

logging.info( "sequitur g2p model:")
with codecs.open('data/dst/speech/%s/sequitur/model-6.test' % options.lang, 'r', 'utf8', 'ignore') as logf:
    for line in logf:
        if not line.startswith('   '):
            continue
        logging.info( line.rstrip())

