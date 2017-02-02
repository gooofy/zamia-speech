#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016 Guenter Bartsch
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
# scan voxforge and kitchen dirs for new audio data and transcripts
# convert to 16kHz wav, add transcripts entries
#

import os
import sys
import logging
import readline
import atexit
import traceback

from optparse import OptionParser
from StringIO import StringIO

import utils
from speech_transcripts import Transcripts

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

#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

#
# config
#

config = utils.load_config()

scan_dirs = []
if lang == 'de':


    scan_dirs.append(config.get("speech", "vf_audiodir_de"))
    scan_dirs.append(config.get("speech", "extrasdir_de"))
    scan_dirs.append(config.get("speech", "gspv2_dir") + '/train')
    scan_dirs.append(config.get("speech", "gspv2_dir") + '/dev')
    # scan_dirs.append(config.get("speech", "gspv2_dir") + '/test')

    wav16_dir   = config.get("speech", "wav16_dir_de")

elif lang == 'en':

    scan_dirs.append(config.get("speech", "vf_audiodir_en"))

    wav16_dir   = config.get("speech", "wav16_dir_en")

else:

    print "***ERROR: language %s not supported yet." % lang
    print
    sys.exit(1)


#
# load transcripts
#

print "loading transcripts..."
transcripts = Transcripts(lang=lang)
print "loading transcripts...done."


def audio_convert (cfn, subdir, fn, audiodir):

    # global mfcc_dir
    global wav16_dir

    # convert audio if not done yet

    w16filename = "%s/%s.wav" % (wav16_dir, cfn)

    if not os.path.isfile (w16filename):

        wavfilename  = "%s/%s/wav/%s.wav" % (audiodir, subdir, fn)

        if not os.path.isfile (wavfilename):
            # flac ?
            flacfilename  = "%s/%s/flac/%s.flac" % (audiodir, subdir, fn)
    
            if not os.path.isfile (flacfilename):
                print "   WAV file '%s' does not exist, neither does FLAC file '%s' => skipping submission." % (wavfilename, flacfilename)
                return False

            print "%-20s: converting %s => %s" % (cfn, flacfilename, '/tmp/foo.wav')
            os.system ("flac -s -f -d '%s' -o /tmp/foo.wav" % flacfilename)
            print "%-20s: converting /tmp/foo.wav => %s (16kHz mono)" % (cfn, w16filename)
            os.system ("sox /tmp/foo.wav -r 16000 -c 1 %s" % w16filename)
            os.system ("rm /tmp/foo.wav")
        
        else:

            print "%-20s: converting %s => %s (16kHz mono)" % (cfn, wavfilename, w16filename)
            os.system ("sox '%s' -r 16000 -c 1 %s" % (wavfilename, w16filename))

    return True

#
# main
#

def scan_audiodir(audiodir):

    global transcripts

    for subdir in os.listdir(audiodir):

        logging.debug ("scanning %s in %s" % (subdir, audiodir))

        subdirfn  = '%s/%s'   % (audiodir, subdir)
        wavdirfn  = '%s/wav'  % subdirfn
        flacdirfn = '%s/flac' % subdirfn

        # do we have prompts?

        prompts = {}

        promptsfn = '%s/etc/prompts-original' % subdirfn
        if os.path.isfile(promptsfn):
            with open(promptsfn) as promptsf:
                while True:
                    line = promptsf.readline().decode('utf8', errors='ignore')
                    if not line:
                        break

                    line = line.rstrip()
                    if '\t' in line:
                        afn = line.split('\t')[0]
                        ts = line[len(afn)+1:]
                    else:
                        afn = line.split(' ')[0]
                        ts = line[len(afn)+1:]

                    prompts[afn] = ts.replace(';',',')

            # print repr(prompts)

        for audiodirfn in [wavdirfn, flacdirfn]:

            if not os.path.isdir(audiodirfn):
                continue

            for audiofullfn in os.listdir(audiodirfn):

                audiofn = audiofullfn.split('.')[0]
                cfn = '%s_%s' % (subdir, audiofn)

                if not cfn in transcripts:
                    # print repr(prompts)
                    prompt = prompts[audiofn] if audiofn in prompts else ''

                    logging.info ("new audio found: %s %s %s" % (cfn, audiofn, prompt))

                    spk     = cfn.split('-')[0]

                    v = { 'dirfn'   : os.path.basename(os.path.normpath(subdirfn)),
                          'audiofn' : audiofn,
                          'prompt'  : prompt,
                          'ts'      : '',
                          'quality' : 0,
                          'spk'     : spk}

                    transcripts[cfn] = v

                audio_convert (cfn, subdir, audiofn, audiodir)

for d in scan_dirs:
    scan_audiodir (d)

print "scanning done."

# print "cleaning transcripts..."
# 
# for cfn in transcripts:
# 
#     transcripts[cfn]['dirfn'] = os.path.basename(os.path.normpath(transcripts[cfn]['dirfn'])) 

transcripts.save()
print "new transcripts saved."
print

