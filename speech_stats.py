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

from speech_transcripts import Transcripts
from speech_lexicon import Lexicon

from nltools.phonetics import ipa2xsampa, xsampa2ipa
from nltools.tokenizer import tokenize
from nltools import misc

LANG = 'de'

#
# init terminal
#

misc.init_app ('speech_stats')

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16_dir_%s" % LANG)


#
# load transcripts
#

print "loading transcripts..."
transcripts = Transcripts(lang=LANG)
print "loading transcripts...done."

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon(lang=LANG)
print "loading lexicon...done."

#
# lexicon stats
#

print
print "%d lexicon entries." % len(lex)

#
# audio stats
#

def format_duration(duration):
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)
    return "%3d:%02d:%02d" % (h, m, s)

total_duration = 0.0
duration_per_spk = {}

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

    duration_per_spk[spk] += duration

    wavef.close()

print
print "total duration of all good submissions: %s" % format_duration(total_duration)
print
print "good submissions per user:"
print
for spk in sorted(duration_per_spk):
    print "%-42s %s" % (spk, format_duration(duration_per_spk[spk]))
print

#
# sphinx model stats
#

print
with codecs.open('data/dst/speech/%s/cmusphinx_cont/logs/sphinxtrain_run.log' % LANG, 'r', 'utf8') as logf:
    for line in logf:
        if 'WORD ERROR RATE' in line:
            print "cmusphinx cont model: %s" % line.strip()
print

print
with codecs.open('data/dst/speech/%s/cmusphinx_ptm/logs/sphinxtrain_run.log' % LANG, 'r', 'utf8') as logf:
    for line in logf:
        if 'WORD ERROR RATE' in line:
            print "cmusphinx ptm model: %s" % line.strip()
print

#
# kaldi model stats
#

print "kaldi models: "
with codecs.open('data/dst/speech/%s/kaldi/RESULTS.txt' % LANG, 'r', 'utf8') as logf:
    for line in logf:
        print line.strip()
print

#
# sequitur model stats
#

print "sequitur g2p model:"
with codecs.open('data/dst/speech/%s/sequitur/model-6.test' % LANG, 'r', 'utf8', 'ignore') as logf:
    for line in logf:
        if not line.startswith('   '):
            continue
        print line.rstrip()
print

