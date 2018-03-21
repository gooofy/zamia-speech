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
import datetime

from optparse               import OptionParser
from nltools                import misc
from nltools.tts            import TTS
from nltools.tokenizer      import tokenize
from nltools.sequiturclient import sequitur_gen_ipa
from nltools.phonetics      import ipa2xsampa, xsampa2ipa
from speech_lexicon         import Lexicon

#
# - play back segments
# - edit/review transcripts
# - add missing words to the dictionary
#

SAMPLE_RATE       = 16000

PROC_TITLE        = 'abook-transcribe'
AUDACITY_DURATION = 3.0
SEQUITUR_MODEL    = 'data/models/sequitur-voxforge-de-latest'

#
# menu subroutines
#

def play_wav():

    global tts, segmentfn

    wavef = wave.open(segmentfn, 'rb')

    num_frames = wavef.getnframes()
    frame_rate = wavef.getframerate()

    duration = float(num_frames) / float(frame_rate)
    wavef.close()

    if duration < AUDACITY_DURATION:
        with open(segmentfn) as wavf:
            wav = wavf.read()
        tts.play_wav(wav, async=True)
    else:
        audacity()

def audacity():

    global tts, segmentfn

    cmd = 'audacity %s &' % segmentfn
    os.system(cmd)

def next_segment():

    global segmentfn
    global prompt

    segmentfn = None
    prompt    = u''

    for fn in sorted(os.listdir(segdirfn)):
        if not fn.endswith('.wav'):
            continue
        segmentfn = '%s/%s' % (segdirfn, fn)
        break

def lex_gen_ipa (lex_base, locale, engine, voice, speak=False):

    global tts

    if engine == 'sequitur':
        ipas = sequitur_gen_ipa (SEQUITUR_MODEL, lex_base)
    
    else:
        tts.locale = locale
        tts.engine = engine
        tts.voice  = voice
        ipas = tts.gen_ipa (lex_base)

    if speak:
        tts.locale = 'de'
        tts.engine = 'mary'
        tts.voice  = 'dfki-pavoque-neutral-hsmm'
        tts.say_ipa(ipas, async=True)

    return ipas

def lex_edit(lex_token):

    global lex, lang

    lex_base  = lex_token.split('_')[0]

    if lex_token in lex:
        lex_entry = lex[lex_token]

    else:
        ipas = lex_gen_ipa(lex_base, 'de', 'sequitur', 'de')
        lex_entry = {'ipa': ipas}
        lex[lex_token] = lex_entry

    ipas = lex_entry['ipa']

    try:
        tts.locale ='de'
        tts.engine ='mary'
        tts.voice  ='dfki-pavoque-neutral-hsmm'
        tts.say_ipa(ipas, async=True)
    except:
        logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

    lex_gen = {}

    lex_gen['de-mary']     = lex_gen_ipa(lex_base, 'de', 'mary',     'bits3')
    lex_gen['de-espeak']   = lex_gen_ipa(lex_base, 'de', 'espeak',   'de')
    lex_gen['de-sequitur'] = lex_gen_ipa(lex_base, 'de', 'sequitur', 'de')

    while True:

        print
        print u"Token       : %s" % lex_token
        print u"IPA         : %s" % lex_entry['ipa']
        print

        for engine in sorted(lex_gen):
            print u"%-11s : %s" % (engine, lex_gen[engine])
        print

        if lex_token in lex:
            m = lex.get_multi(lex_token)
            for k in m:
                print u"%s [%s]" % (k, m[k]['ipa'])

        else:
            print u"NEW TOKEN"

        print u"SPEAK  P:de-unitsel  O:de-hsmm                   I:fr-hsmm   U:en-hsmm"
        print u"GEN    G:de-mary     H:de-espeak  J:de-sequitur  K:fr-mary   L:en-mary"
        print u"       E:Edit        Q:Quit "

        try:

            resp = raw_input("Lex> ")

            # quit
            if resp.lower() == 'q':
                break  
        
            # generate de-mary
            elif resp.lower() == 'g':
                lex_entry['ipa'] = lex_gen_ipa (lex_base, 'de', 'mary', 'bits3', True)

            # generate de-espeak
            elif resp.lower() == 'h':
                lex_entry['ipa'] = lex_gen_ipa (lex_base, 'de', 'espeak', 'de', True)
                
            # generate en-mary 
            elif resp.lower() == 'l':
                
                tts.locale ='en-US'
                tts.engine ='mary'
                tts.voice  ='cmu-rms-hsmm'

                ipas = tts.gen_ipa (lex_base)
                tts.say_ipa(ipas, async=True)
                lex_entry['ipa'] = ipas

            # generate fr-mary 
            elif resp.lower() == 'k':
                
                tts.locale ='fr'
                tts.engine ='mary'
                tts.voice  ='upmc-pierre-hsmm'

                ipas = tts.gen_ipa (lex_base)
                tts.say_ipa(ipas, async=True)
                lex_entry['ipa'] = ipas

            # generate de-sequitur
            elif resp.lower() == 'j':
                lex_entry['ipa'] = lex_gen_ipa (lex_base, 'de', 'sequitur', 'de', True)
                
            # speak de mary unitsel 
            elif resp.lower() == 'p':
        
                if len(lex_entry['ipa']) == 0:
                    continue
        
                ipas = lex_entry['ipa']

                tts.locale ='de'
                tts.engine ='mary'
                tts.voice  ='bits3'

                tts.say_ipa(ipas, async=True)

            # speak de mary hsmm
            elif resp.lower() == 'o':
        
                if len(lex_entry['ipa']) == 0:
                    continue
        
                ipas = lex_entry['ipa']

                tts.locale = 'de'
                tts.engine = 'mary'
                tts.voice  = 'dfki-pavoque-neutral-hsmm'

                tts.say_ipa(ipas, async=True)

            # speak fr mary hsmm
            elif resp.lower() == 'i':
       
                if len(lex_entry['ipa']) == 0:
                    continue
        
                ipas = lex_entry['ipa']

                tts.locale ='fr'
                tts.engine ='mary'
                tts.voice  ='upmc-pierre-hsmm'

                tts.say_ipa(ipas, async=True)
       
            # speak en mary hsmm
            elif resp.lower() == 'u':
        
                ipas = lex_entry['ipa']

                tts.locale = 'en-US'
                tts.engine = 'mary'
                tts.voice  = 'cmu-rms-hsmm'

                tts.say_ipa(ipas, async=True)
       
            # edit XS
            elif resp.lower() == 'e':
        
                ipas = lex_entry['ipa']

                xs = ipa2xsampa (lex_token, ipas, stress_to_vowels=False)
                xs = raw_input(xs + ' ')

                ipas = xsampa2ipa (lex_token, xs)
    
                lex_entry['ipa'] = ipas

        except:
            logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

    lex.save()
    print "new lexicon saved."
    print

#
# init terminal
#

misc.init_app (PROC_TITLE)

readline.set_history_length(1000)

#
# command line
#

parser = OptionParser("usage: %prog [options] segmentsdir")

parser.add_option("-s", "--speaker1", dest="speaker1", type = "str", default='alice',
                  help="speaker #1 (default: alice)")
parser.add_option("-S", "--speaker2", dest="speaker2", type = "str", default='bob',
                  help="speaker #2 (default: bob)")
parser.add_option("-l", "--lang", dest="lang", type = "str", default='de',
                  help="language (default: de)")
parser.add_option("-o", "--out-dir", dest="outdir", type = "str", default='abook/out',
                  help="language (default: abook/out)")
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

lang      = options.lang
segdirfn  = args[0]
speaker1  = options.speaker1
speaker2  = options.speaker2

# wavdirfn  = '%s/wav' % subdirfn
# promptsfn = '%s/etc/prompts-original' % subdirfn

#
# config
#

config = misc.load_config('.speechrc')

vf_login    = config.get("speech", "vf_login")
extrasdir   = config.get("speech", "extrasdir_%s" % lang)

#
# TTS (for audio output)
#

tts = TTS ('local', 0, locale='de', voice='bits3', engine='espeak')

#
# load lexicon
#

logging.info("loading lexicon...")
lex = Lexicon(lang=options.lang)
logging.info("loading lexicon...done.")

#
# main ui loop
#

next_segment()

while segmentfn:

    print
    print segmentfn
    print prompt

    # any words not covered by our lexicon?

    lex_missing = set()

    tokens = tokenize(prompt, lang=lang)
    ts = u' '.join(tokens)
    print ts

    for t in tokens:
        if not t in lex:
            lex_missing.add(t)
    if lex_missing:
        print
        print u"missing tokens: %s" % repr(sorted(lex_missing))

    print
        
    resp = raw_input("P:Play A:Audacity E:Edit L:Lex 1:%s 2:%s 0:Delete Q:Quit >" % (speaker1, speaker2))

    if resp.lower() == 'q':
        break
   
    if resp.lower() == '0':
        os.remove(segmentfn)
        next_segment()

    if resp.lower() == 'p':
        play_wav()

    if resp.lower() == 'a':
        audacity()

    if resp.lower() == 'e':
        prompt = raw_input("Prompt> ")

    if resp.lower() == 'l':
        if not lex_missing:
            print "All words are covered by the dictionary."
            continue
        lex_edit(list(lex_missing)[0])

    if resp == '1' or resp == '2':
        if lex_missing:
            print "Not all words are covered by the dictionary."
            continue

        speaker = options.speaker1 if resp == '1' else options.speaker2

        # does a directory for recordings of this speaker already exist?

        speakerdirfn = None
        for fn in os.listdir(options.outdir):
            if fn.startswith(speaker):
                speakerdirfn = '%s/%s' % (options.outdir, fn)
                break
        if not speakerdirfn:
            ds = datetime.date.strftime(datetime.date.today(), '%Y%m%d')
            speakerdirfn = '%s/%s-%s-rec' % (options.outdir, speaker, ds)

        misc.mkdirs('%s/wav' % speakerdirfn)
        misc.mkdirs('%s/etc' % speakerdirfn)

        destfn = '%s/wav/%s' % (speakerdirfn, os.path.basename(segmentfn))
        os.rename(segmentfn, destfn)
        print "moved %s to %s" % (segmentfn, destfn)

        promptsfn = '%s/etc/prompts-original' % speakerdirfn
        with codecs.open(promptsfn, 'a', 'utf8') as promptsf:
            wavbn = os.path.basename(segmentfn)
            wavbn = os.path.splitext(wavbn)[0]
            promptsf.write(u'%s %s\n' % (wavbn, prompt))
        print "%s written." % promptsfn

        next_segment()


        

