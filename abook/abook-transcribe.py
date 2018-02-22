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
import logging
import re
import readline
import wave

from optparse           import OptionParser
from nltools            import misc
from nltools.tts        import TTS

#
# - play back segments
# - edit/review transcripts
#

SAMPLE_RATE       = 16000

PROC_TITLE        = 'abook-transcribe'
AUDACITY_DURATION = 3.0

def play_wav(pid):

    global wavdirfn, tts

    wavfn = '%s/%s.wav' % (wavdirfn, pid)

    wavef = wave.open(wavfn, 'rb')

    num_frames = wavef.getnframes()
    frame_rate = wavef.getframerate()

    duration = float(num_frames) / float(frame_rate)
    wavef.close()

    if duration < AUDACITY_DURATION:
        with open(wavfn) as wavf:
            wav = wavf.read()
        tts.play_wav(wav, async=True)
    else:
        audacity(pid)

def audacity(pid):

    global wavdirfn, tts

    wavfn = '%s/%s.wav' % (wavdirfn, pid)

    cmd = 'audacity %s &' % wavfn
    os.system(cmd)

#
# init terminal
#

misc.init_app (PROC_TITLE)

readline.set_history_length(1000)

#
# config
#

config = misc.load_config('.speechrc')

vf_login    = config.get("speech", "vf_login")

#
# command line
#

parser = OptionParser("usage: %prog [options] directory")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

subdirfn  = args[0]
wavdirfn  = '%s/wav' % subdirfn
promptsfn = '%s/etc/prompts-original' % subdirfn

#
# TTS (for wav output)
#

tts = TTS ('local', 0, locale='de', voice='bits3', engine='espeak')

#
# collect wav files
#

wavs = []
for fn in os.listdir(wavdirfn):
    if not fn.endswith('.wav'):
        continue
    wavs.append(fn[:len(fn)-4])

#
# load prompts
#

prompts = {}

prexp = re.compile(r"(\S+)\s(.*)$")

if os.path.isfile(promptsfn):
    with codecs.open(promptsfn, 'r', 'utf8') as promptsf:
        for line in promptsf:
            m = prexp.match(line.strip())
            if not m:
                logging.error('failed to parse prompts line: %s' % repr(line))
                continue
            
            pid = m.group(1)
            prompt = m.group(2)

            prompts[pid] = prompt

# print repr(wavs), repr(prompts)

#
# main ui loop
#

idx = 0
while idx < len(wavs):
    pid = wavs[idx]
    if not pid in prompts:
        break
    idx += 1

while True:

    pid = wavs[idx]

    if pid in prompts:
        print 
        print prompts[pid]
        
    resp = raw_input("%s (L)isten (A)udacity (E)dit (N)ext (P)rev (Q)uit>" % pid)

    if resp.lower() == 'q':
        break
   
    if resp.lower() == 'n':
        idx += 1
        if idx >= len(wavs):
            idx = len(wavs)-1
        pid = wavs[idx]
        play_wav(pid)

    if resp.lower() == 'p':
        idx -= 1
        if idx<0:
            idx = 0
        pid = wavs[idx]
        play_wav(pid)

    if resp.lower() == 'l':
        pid = wavs[idx]
        play_wav(pid)

    if resp.lower() == 'a':
        pid = wavs[idx]
        audacity(pid)

    if resp.lower() == 'e':
        prompts[pid] = raw_input("%s prompt>" % pid)

#
# re-write prompts file
#

with codecs.open(promptsfn, 'w', 'utf8') as promptsf:
    for pid in wavs:
        if pid in prompts:
            prompt = prompts[pid]
        else:
            prompt = u""
        promptsf.write(u'%s %s\n' % (pid, prompt))

logging.info ('%s written.' % promptsfn)


