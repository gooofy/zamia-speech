#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017, 2018 Guenter Bartsch
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
# interactive all-in-one readline application for audio review, transcription 
# and lexicon editing
#

import os
import sys
import logging
import traceback
import readline
import locale
import codecs
import random

from optparse               import OptionParser

from nltools                import misc
from nltools.phonetics      import ipa2xsampa, xsampa2ipa
from nltools.tokenizer      import tokenize
from nltools.sequiturclient import sequitur_gen_ipa
from nltools.tts            import TTS

from speech_transcripts     import Transcripts
from speech_lexicon         import Lexicon

PROC_TITLE      = 'speech_editor'
DEFAULT_MARY    = False # switch between mary and sequitur default g2p
SEQUITUR_MODEL  = 'data/models/sequitur-dict-de.ipa-latest'
DEFAULT_DICT    = 'dict-de.ipa'
DEFAULT_WRT     = 'data/src/wrt/librivox_de.csv'

PUNCTUATION = set([',','.','\'','!','?','"','-'])

def tokwrt (ts):

    global options, wrt

    res = []
    for t in tokenize(ts, lang=options.lang, keep_punctuation=options.keep_punctuation):
        if t in wrt:
            res.append(wrt[t])
        else:
            res.append(t)
    return res

def play_wav(ts):

    global wav16_dir, tts, corpus_name

    wavfn = '%s/%s/%s.wav' % (wav16_dir, corpus_name, ts['cfn'])

    with open(wavfn) as wavf:
        wav = wavf.read()

    tts.play_wav(wav, async=True)

def goto_next_ts(cur_ts):

    global edit_ts, options

    if options.random:

        # still un-reviewed ts left?
        ur = False
        for ts in edit_ts:
            if ts['quality']==0:
                ur = True
                break

        if ur:
            cur_ts = random.randint(0, len(edit_ts)-1)
            while edit_ts[cur_ts]['quality'] > 0:
                cur_ts = (cur_ts + 1) % len(edit_ts)


    else:
        cur_ts = (cur_ts + 1) % len(edit_ts)

    missing_token = paint_main(cur_ts)
    ts = edit_ts[cur_ts]
    play_wav(ts)

    return missing_token, cur_ts

def accept_ts(qty, cur_ts):

    global edit_ts

    edit_ts[cur_ts]['quality'] = qty


#
# Lex Editor
#

def lex_paint_main():

    global lex_token, lex, lex_entry

    print
    print u"Token : %s" % lex_token
    print u"  IPA : %s" % lex_entry['ipa']
    print

    if lex_token in lex:
        m = lex.get_multi(lex_token)
        for k in m:
            print u"   lex: %s [%s]" % (k, m[k]['ipa'])

    else:
        print "   NEW TOKEN"

    print
    print "SPEAK  p:de-unitsel  o:de-hsmm                   i:fr-hsmm   u:en-hsmm"
    print "GEN    g:de-mary     h:de-espeak  j:de-sequitur  k:fr-mary   l:en-mary           e:edit  t:token       q:quit"
    print

def lex_set_token(token):

    global lex, lex_token, lex_entry, lex_base

    tts.locale = 'de'
    tts.engine = 'mary'
    tts.voice  = 'bits3'

    lex_token = token
    lex_base  = token.split('_')[0]

    if lex_token in lex:

        lex_entry = lex[lex_token]

    else:

        if DEFAULT_MARY:
            ipas = tts.gen_ipa (lex_base)
        else:
            ipas = sequitur_gen_ipa (SEQUITUR_MODEL, lex_base)

        lex_entry = {'ipa': ipas}
        lex[lex_token] = lex_entry

    ipas = lex_entry['ipa']

    try:
        tts.say_ipa(ipas)
    except:
        logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())


def lex_edit(token):

    global lex, lex_token, lex_entry, lex_base

    lex_set_token (token)

    while True:
   
        try:

            lex_paint_main()
       
            c = raw_input('lex > ').lower() 
            if c == 'q':
                lex.save()
                break  
        
            # generate de-mary
            elif c == 'g':
                
                tts.locale = 'de'
                tts.engine = 'mary'
                tts.voice  = 'bits3'

                ipas = tts.gen_ipa (lex_base)
                tts.say_ipa(ipas)
                lex_entry['ipa'] = ipas
       
            # generate de-espeak
            elif c == 'h':
                
                tts.locale ='de'
                tts.engine ='espeak'
                tts.voice  ='de'
                ipas = tts.gen_ipa (lex_base)
                lex_entry['ipa'] = ipas

                tts.locale ='de'
                tts.engine ='mary'
                tts.voice  ='bits3'
                tts.say_ipa(ipas)

        
            # generate en-mary 
            elif c == 'l':
                
                tts.locale ='en-US'
                tts.engine ='mary'
                tts.voice  ='cmu-rms-hsmm'

                ipas = tts.gen_ipa (lex_base)
                tts.say_ipa(ipas)
                lex_entry['ipa'] = ipas

            # generate fr-mary 
            elif c == 'k':
                
                tts.locale ='fr'
                tts.engine ='mary'
                tts.voice  ='upmc-pierre-hsmm'

                ipas = tts.gen_ipa (lex_base)
                tts.say_ipa(ipas)
                lex_entry['ipa'] = ipas

            # generate de-sequitur
            elif c == 'j':
                
                ipas = sequitur_gen_ipa (SEQUITUR_MODEL, lex_base)
                tts.locale ='de'
                tts.engine ='mary'
                tts.voice  ='bits3'
                tts.say_ipa(ipas)
                lex_entry['ipa'] = ipas

            # speak de mary unitsel 
            elif c == 'p':
        
                if len(lex_entry['ipa']) == 0:
                    continue
        
                ipas = lex_entry['ipa']

                tts.locale = 'de'
                tts.engine = 'mary'
                tts.voice  = 'bits3'

                tts.say_ipa(ipas)

            # speak de mary hsmm
            elif c == 'o':
        
                if len(lex_entry['ipa']) == 0:
                    continue
        
                ipas = lex_entry['ipa']

                tts.locale = 'de'
                tts.engine = 'mary'
                tts.voice  = 'dfki-pavoque-neutral-hsmm'

                tts.say_ipa(ipas)

            # speak fr mary hsmm
            elif c == 'i':
       
                if len(lex_entry['ipa']) == 0:
                    continue
        
                ipas = lex_entry['ipa']

                tts.locale = 'fr'
                tts.engine = 'mary'
                tts.voice  = 'pierre-voice-hsmm'

                tts.say_ipa(ipas)
       
            # speak en mary hsmm
            elif c == 'u':
        
                ipas = lex_entry['ipa']

                tts.locale = 'en-US'
                tts.engine = 'mary'
                tts.voice  = 'cmu-rms-hsmm'

                tts.say_ipa(ipas)
       
            # edit token
            elif c == 't':

                readline.add_history(lex_token.encode('utf8'))
                token = raw_input('token: ').decode('utf8')

                lex_set_token (token)

            # edit XS
            elif c == 'e':
        
                ipas = lex_entry['ipa']

                xs = ipa2xsampa (lex_token, ipas, stress_to_vowels=False)

                readline.add_history(xs.encode('utf8'))
                xs = raw_input('X-SAMPA: ').decode('utf8')

                ipas = xsampa2ipa (lex_token, xs)
        
                lex_entry['ipa'] = ipas

        except:
            logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

#
# init
#

misc.init_app(PROC_TITLE)
readline.set_history_length(1000)

#
# command line
#

parser = OptionParser("usage: %prog [options] <corpus> [filters])")

parser.add_option ("-d", "--dict", dest="dict_name", type = "str", default=DEFAULT_DICT,
                   help="dictionary to work on (default: %s)" % DEFAULT_DICT)

parser.add_option("-p", "--prompts", dest="promptsfn",
                  help="read prompts from FILE", metavar="FILE")

parser.add_option("-l", "--lang", dest="lang", type = "str", default='de',
                  help="language (default: de)")

parser.add_option("-k", "--keep-punctuation", action="store_true", dest="keep_punctuation", 
                  help="keep punctuation marks")

parser.add_option("-m", "--missing-words", action="store_true", dest="missing_words", 
                  help="only work on submissions that have at least one missing word")

parser.add_option("-r", "--random", action="store_true", dest="random", 
                  help="random mode")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

parser.add_option("-w", "--wrt", dest="wrt", type = "str", default=DEFAULT_WRT,
                  help="word replacement table (default: %s)" % DEFAULT_WRT)


(options, args) = parser.parse_args()

if len(args)<1:
    parser.print_help()
    sys.exit(1)

corpus_name = args[0]

ts_filters = [ a.decode('utf8') for a in args[1:] ]

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# load WRT
#

wrt = {}

logging.info('loading WRT from %s ...' % options.wrt)

with codecs.open(options.wrt, 'r', 'utf8') as wrtf:
    for line in wrtf:
        parts = line.strip().split(';')
        if len(parts) != 2:
            continue
        wrt[parts[0]] = parts[1]

logging.info(repr(wrt))

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=corpus_name)
logging.info("loading transcripts...done.")

#
# load lexicon
#

logging.info("loading lexicon...")
lex = Lexicon(file_name=options.dict_name)
logging.info("loading lexicon...done.")

#
# load prompts
#

prompt_tokens    = []
prompt_token_idx = 0
if options.promptsfn:
    with codecs.open(options.promptsfn, 'r', 'utf8') as promptsf:
        for line in promptsf:
            prompt_tokens.extend(tokwrt(line))

    logging.info("%s read. %d tokens." % (options.promptsfn, len(prompt_tokens)))

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16")
host        = config.get('tts', 'host')
port        = int(config.get('tts', 'port'))

#
# TTS
#

tts = TTS (host, port, locale='de', voice='bits3', engine='espeak')

def paint_main(cur_ts):

    global edit_ts, prompt_tokens, prompt_token_idx

    ts = edit_ts[cur_ts]

    # header

    print
    print u"%5d/%5d %s QLTY: %d" % (cur_ts+1, len(edit_ts), ts['cfn'], ts['quality'])

    # prompts file

    if prompt_token_idx < len(prompt_tokens):
        print 
        print u"prompts file: %s" % u' '.join(prompt_tokens[prompt_token_idx:prompt_token_idx+8])

    # body / transcript

    print
    print u"%s" % ts['prompt']
    print

    if len(ts['ts']) == 0:
        ts['ts'] = ' '.join(tokwrt(ts['prompt']))

    missing_token = None

    for token in ts['ts'].split(' '):

        if token in lex:

            s = u''

            m = lex.get_multi(token)

            for t in m:

                v = m[t]

                if len(s) > 0:
                    s += u', '

                if len(m)>1 and t == token:
                    s += u'**'
                s += t
                s += u' [' + m[t]['ipa']
                s += u']'

            print u"           %s" % s
            
        else:
            if token in PUNCTUATION:
                print u"           %s" % token
    
            else:
                if not missing_token:
                    missing_token = token

                print u"  MISSING  %s" % token

    # menu

    print
    print "p:play     e:prompt  t:transcript                        accept: 1=poor 2=fair 3=good"
    print "l:lex      w:wrt     prompts file: a=add s=skip b=back                         q:quit"
    print

    return missing_token

#
# main 
#

try:

    # apply filter:

    edit_ts = []
    for cfn in transcripts:

        ts = transcripts[cfn]

        if ts['quality'] != 0:
            continue

        tsf_matched = False
        for tsf in ts_filters:
            if (tsf in cfn) or (tsf in ts['prompt'].lower()):
                tsf_matched = True 

        if not ts_filters or tsf_matched:

            if options.missing_words:

                missing = False

                t = ts['ts']
                if len(t) == 0:
                    t = ' '.join(tokwrt(ts['prompt']))
                    
                for token in t.split(' '):

                    if (not token in lex) and (not token in PUNCTUATION) :
                        missing = True
                        break

                if missing:
                    edit_ts.append(ts)

            else:
                edit_ts.append(ts)
        
        if options.random and len(edit_ts)>0:
            cur_ts = random.randint(0, len(edit_ts)-1)
        else:
            cur_ts = 0

    if len(edit_ts) == 0:
        raise Exception ('no submissions found!')

    while True:
    
        ts = edit_ts[cur_ts]

        missing_token = paint_main(cur_ts)

        c = raw_input('%s > ' % missing_token)
        if not c:
            break

        c = c.strip().lower()

        if c == 'q':
            break  
   
        elif c == 'p':
            play_wav(ts)

        elif c == '1':
            accept_ts(1, cur_ts)
            missing_token, cur_ts = goto_next_ts(cur_ts)
        elif c == '2':
            if not missing_token:
                accept_ts(2, cur_ts)
                missing_token, cur_ts = goto_next_ts(cur_ts)
        elif c == '3':
            if not missing_token:
                accept_ts(3, cur_ts)
                missing_token, cur_ts = goto_next_ts(cur_ts)
                    
        elif c == 'e':

            readline.add_history(ts['prompt'].encode('utf8'))
            ts['prompt'] = raw_input('prompt: ').decode('utf8')
            ts['ts'] = ''

        elif c == 't':

            readline.add_history(ts['ts'].encode('utf8'))
            ts['ts'] = raw_input('transcript: ').decode('utf8')

        elif c == 'a':

            if prompt_token_idx < len(prompt_tokens):
                if len(ts['prompt']) > 0:
                    ts['prompt'] += ' '
                ts['prompt'] +=  prompt_tokens[prompt_token_idx]
                ts['ts'] = ''
                prompt_token_idx += 1

        elif c == 's':

            if prompt_token_idx < len(prompt_tokens):
                prompt_token_idx += 1

        elif c == 'b':

            if prompt_token_idx >0:

                prompt_token_idx -= 1

                cur_tokens = tokwrt(ts['ts'])

                if len(cur_tokens)>1:
                    ts['prompt'] = ' '.join(cur_tokens[0:len(cur_tokens)-1])
                else:
                    ts['prompt'] = ''
                ts['ts'] = ''

        elif c == 'l':

            if len(ts['ts'])>0 or missing_token:

                if missing_token:
                    t = missing_token
                else:
                    t = tokwrt(ts['ts'])[0]

                lex_edit(t)


    transcripts.save()
    logging.info("new transcripts saved.")

    lex.save()
    logging.info("new lexicon saved.")

except:
    logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

