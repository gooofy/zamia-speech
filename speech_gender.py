#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017 Guenter Bartsch
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
# interactive spk2gender editor
#

import os
import sys
import logging
import traceback
import locale

from optparse           import OptionParser

from nltools            import misc
from nltools.tts        import TTS
from speech_transcripts import Transcripts

def play_wav(cfn):

    global wav16_dir, tts

    wavfn = '%s/%s.wav' % (wav16_dir, cfn)

    with open(wavfn) as wavf:
        wav = wavf.read()

    tts.play_wav(wav, async=True)

#
# init 
#

misc.init_app ('speech_gender')

config = misc.load_config ('.speechrc')

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

#
# commandline
#

parser = OptionParser("usage: %prog [options] ")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
           help="language (default: de)")

(options, args) = parser.parse_args()

lang = options.lang

SPK2GENDERFN = 'data/src/speech/%s/spk2gender' % lang

#
# load spk2gender
#

spk2gender = {}

print "loading %s..." % SPK2GENDERFN
with open(SPK2GENDERFN, 'r') as f:

    for line in f:
        parts = line.strip().split(' ')
        spk2gender[parts[0].strip()] = parts[1].strip()
        
print "loading %s ...done." % SPK2GENDERFN

#
# load transcripts
#

print "loading transcripts..."
transcripts = Transcripts(lang=lang)
print "loading transcripts...done."

#
# config
#

wav16_dir   = config.get("speech", "wav16_dir_%s" % lang)
host        = config.get('tts', 'host')
port        = int(config.get('tts', 'port'))

#
# TTS
#

tts = TTS (host, port, locale='de', voice='bits3')

#
# count
#

known = set()
for spk in spk2gender:
    known.add(spk)

num_unk = 0
for cfn in transcripts:

    ts = transcripts[cfn]
    spk = ts['spk']

    if spk in known:
        continue

    num_unk += 1

    print '%5d %s' % (num_unk, spk)

    known.add(spk)

#
# main 
#

cnt = 0
for cfn in transcripts:

    ts = transcripts[cfn]

    if ts['spk'] in spk2gender:
        continue

    cnt += 1
    wavfn = '%s/%s.wav' % (wav16_dir, cfn)
    print '%5d/%5d' % (cnt, num_unk), ts['spk'], wavfn
    play_wav(cfn)

    reply = raw_input('m/f/q >')

    if reply == 'q' or reply=='Q':
        break

    spk2gender[ts['spk']] = reply

    with open(SPK2GENDERFN, 'w') as f:

        for spk in sorted(spk2gender):
            f.write('%s %s\n' % (spk, spk2gender[spk]))

    print "%s written." % SPK2GENDERFN

