#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016 Guenter Bartsch
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
# interactive all-in-one curses application for audio review, transcription 
# and lexicon editing
#

import os
import sys
import logging
import traceback
import curses
import curses.textpad
import locale
import codecs

from optparse import OptionParser

import utils
from speech_transcripts import Transcripts
from speech_lexicon import Lexicon, ipa2xsampa, xsampa2ipa
from speech_tokenizer import tokenize
from speech_sequitur import sequitur_gen_ipa
from tts_client import TTSClient

DEFAULT_MARY = False # switch between mary and sequitur default g2p

def play_wav(ts):

    global wav16_dir, tts

    wavfn = '%s/%s.wav' % (wav16_dir, ts['cfn'])

    with open(wavfn) as wavf:
        wav = wavf.read()

    tts.play_wav(wav)

def goto_next_ts(cur_ts):

    global edit_ts

    cur_ts = (cur_ts + 1) % len(edit_ts)
    missing_token = paint_main(stdscr, cur_ts)
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

    global stdscr, lex_token, lex, lex_entry

    stdscr.clear()

    my, mx = stdscr.getmaxyx()

    for x in range(mx):
        stdscr.insstr(   0, x, ' ', curses.A_REVERSE)
        stdscr.insstr(my-2, x, ' ', curses.A_REVERSE)
        stdscr.insstr(my-1, x, ' ', curses.A_REVERSE)

    stdscr.insstr(0, mx-15, "Lexicon Editor", curses.A_REVERSE )

    stdscr.insstr(4, 2, ("Token : %s" % lex_token).encode('utf8'))
    stdscr.insstr(5, 2, ("  IPA : %s" % lex_entry['ipa']).encode('utf8'))

    if lex_token in lex:

        m = lex.get_multi(lex_token)
        cy = 10
        for k in m:
            stdscr.insstr(cy, 4, ("%s [%s]" % (k, m[k]['ipa'])).encode('utf8'))
            cy += 1

    else:
        stdscr.insstr(10, 4, "NEW TOKEN")

    stdscr.insstr(my-2, 0, "SPEAK  P:de-unitsel  O:de-hsmm                   I:fr-hsmm   U:en-hsmm", curses.A_REVERSE )
    stdscr.insstr(my-1, 0, "GEN    G:de-mary     H:de-espeak  J:de-sequitur  K:fr-mary   L:en-mary", curses.A_REVERSE )
    stdscr.insstr(my-2, mx-40, "                                        ", curses.A_REVERSE )
    stdscr.insstr(my-1, mx-40, "           E:Edit  T:Token       Q:Quit ", curses.A_REVERSE )
    stdscr.refresh()

def lex_set_token(token):

    global lex, lex_token, lex_entry, lex_base

    tts.set_locale ('de')
    tts.set_engine ('mary')
    tts.set_voice ('bits3')

    lex_token = token
    lex_base  = token.split('_')[0]

    if lex_token in lex:

        lex_entry = lex[lex_token]

    else:

        if DEFAULT_MARY:
            ipas = tts.gen_ipa (lex_base)
        else:
            ipas = sequitur_gen_ipa (lex_base)

        lex_entry = {'ipa': ipas}
        lex[lex_token] = lex_entry

    ipas = lex_entry['ipa']

    tts.say_ipa(ipas)




def lex_edit(token):

    global lex, lex_token, lex_entry, lex_base

    lex_set_token (token)

    while True:
    
        lex_paint_main()
    
        c = stdscr.getch()
        if c == ord('q'):
            lex.save()
            break  
    
        # generate de-mary
        elif c == ord('g'):
            
            tts.set_locale ('de')
            tts.set_engine ('mary')
            tts.set_voice ('bits3')

            ipas = tts.gen_ipa (lex_base)
            tts.say_ipa(ipas)
            lex_entry['ipa'] = ipas
   
        # generate de-espeak
        elif c == ord('h'):
            
            tts.set_locale ('de')
            tts.set_engine ('espeak')
            tts.set_voice  ('de')
            ipas = tts.gen_ipa (lex_base)

            tts.set_locale ('de')
            tts.set_engine ('mary')
            tts.set_voice ('bits3')
            tts.say_ipa(ipas)

            lex_entry['ipa'] = ipas
    
        # generate en-mary 
        elif c == ord('l'):
            
            tts.set_locale ('en-US')
            tts.set_engine ('mary')
            tts.set_voice ('cmu-rms-hsmm')

            ipas = tts.gen_ipa (lex_base)
            tts.say_ipa(ipas)
            lex_entry['ipa'] = ipas

        # generate fr-mary 
        elif c == ord('k'):
            
            tts.set_locale ('fr')
            tts.set_engine ('mary')
            tts.set_voice ('upmc-pierre-hsmm')

            ipas = tts.gen_ipa (lex_base)
            tts.say_ipa(ipas)
            lex_entry['ipa'] = ipas

        # generate de-sequitur
        elif c == ord('j'):
            
            ipas = sequitur_gen_ipa (lex_base)
            tts.set_locale ('de')
            tts.set_engine ('mary')
            tts.set_voice ('bits3')
            tts.say_ipa(ipas)
            lex_entry['ipa'] = ipas

        # speak de mary unitsel 
        elif c == ord('p'):
    
            if len(lex_entry['ipa']) == 0:
                continue
    
            ipas = lex_entry['ipa']

            tts.set_locale ('de')
            tts.set_engine ('mary')
            tts.set_voice ('bits3')

            tts.say_ipa(ipas)

        # speak de mary hsmm
        elif c == ord('o'):
    
            if len(lex_entry['ipa']) == 0:
                continue
    
            ipas = lex_entry['ipa']

            tts.set_locale ('de')
            tts.set_engine ('mary')
            tts.set_voice ('dfki-pavoque-neutral-hsmm')

            tts.say_ipa(ipas)

        # speak fr mary hsmm
        elif c == ord('i'):
   
            if len(lex_entry['ipa']) == 0:
                continue
    
            ipas = lex_entry['ipa']

            tts.set_locale ('fr')
            tts.set_engine ('mary')
            tts.set_voice ('pierre-voice-hsmm')

            tts.say_ipa(ipas)
   
        # speak en mary hsmm
        elif c == ord('u'):
    
            ipas = lex_entry['ipa']

            tts.set_locale ('en-US')
            tts.set_engine ('mary')
            tts.set_voice ('cmu-rms-hsmm')

            tts.say_ipa(ipas)
   
        # edit token
        elif c == ord('t'):

            token = utils.edit_popup(stdscr, ' Token ', '')

            lex_set_token (token)

        # edit XS
        elif c == ord('e'):
    
            ipas = lex_entry['ipa']

            xs = ipa2xsampa (lex_token, ipas, stress_to_vowels=False)

            xs = utils.edit_popup(stdscr, ' X-SAMPA ', xs)

            try:
                ipas = xsampa2ipa (lex_token, xs)
    
                lex_entry['ipa'] = ipas
            except:
                pass



logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

#
# command line
#

parser = OptionParser("usage: %prog [options] [filter])")

parser.add_option("-p", "--prompts", dest="promptsfn",
                  help="read prompts from FILE", metavar="FILE")

parser.add_option("-m", "--missing-words", action="store_true", dest="missing_words", 
                  help="only work on submissions that have at least one missing word")


(options, args) = parser.parse_args()

ts_filter = None

if len(args)==1:
    ts_filter = args[0].decode('utf8')

#
# load transcripts
#

print "loading transcripts..."
transcripts = Transcripts()
print "loading transcripts...done."

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

#
# load prompts
#

prompt_tokens    = []
prompt_token_idx = 0
if options.promptsfn:
    with codecs.open(options.promptsfn, 'r', 'utf8') as promptsf:
        for line in promptsf:
            prompt_tokens.extend(tokenize(line))

    print "%s read. %d tokens." % (options.promptsfn, len(prompt_tokens))

#
# curses
#

locale.setlocale(locale.LC_ALL,"")

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(1)

#
# config
#

config = utils.load_config()

wav16_dir   = config.get("speech", "wav16_dir_de")
host        = config.get('tts', 'host')
port        = int(config.get('tts', 'port'))

#
# TTS Client
#

tts = TTSClient (host, port, locale='de', voice='bits3')

def paint_main(stdscr, cur_ts):

    global edit_ts, prompt_tokens, prompt_token_idx

    ts = edit_ts[cur_ts]

    stdscr.clear()

    my, mx = stdscr.getmaxyx()

    for x in range(mx):
        stdscr.insstr(   0, x, ' ', curses.A_REVERSE)
        stdscr.insstr(my-2, x, ' ', curses.A_REVERSE)
        stdscr.insstr(my-1, x, ' ', curses.A_REVERSE)

    # header

    s = u"%2d/%2d %-30s QTY: %d" % (cur_ts+1, len(edit_ts), ts['cfn'], ts['quality'])

    stdscr.insstr(0, 0, s.encode('utf8'), curses.A_BOLD | curses.A_REVERSE )
    stdscr.insstr(0, mx-13, 'Speech Editor', curses.A_REVERSE)

    # prompts file

    if prompt_token_idx < len(prompt_tokens):
        pstr = ' '.join(prompt_tokens[prompt_token_idx:prompt_token_idx+8])
        stdscr.insstr(1, mx-len(pstr), pstr.encode('utf8'))

    # body / transcript

    stdscr.insstr(2, 0, 'Prompt:', curses.A_BOLD)
    stdscr.insstr(3, 0, ts['prompt'].encode('utf8'))

    if len(ts['ts']) == 0:
        ts['ts'] = ' '.join(tokenize(ts['prompt']))

    cy = 5
    cx = 0

    missing_token = None

    for token in ts['ts'].split(' '):

        if token in lex:

            s = ''

            m = lex.get_multi(token)

            for t in m:

                v = m[t]

                if len(s) > 0:
                    s += ', '

                if len(m)>1 and t == token:
                    s += '**'
                s += t
                s += ' [' + m[t]['ipa']
                s += ']'

            stdscr.insstr(cy, cx, s.encode('utf8') )
            
        else:
            if not missing_token:
                missing_token = token

            stdscr.insstr(cy, cx, token.encode('utf8'), curses.A_REVERSE)

        cy += 1
        if cy > my-2:
            break
        

    # footer

    stdscr.insstr(my-2, 0,     " P:Play     E:Prompt  T:Transcript                      ", curses.A_REVERSE )
    stdscr.insstr(my-1, 0,     " L:LexEdit            Prompts File: A=add S=skip B=Back ", curses.A_REVERSE )
    stdscr.insstr(my-2, mx-40, "           Accept: 1=Poor 2=Fair 3=Good ", curses.A_REVERSE )
    stdscr.insstr(my-1, mx-40, "                                 Q:Quit ", curses.A_REVERSE )
    stdscr.refresh()

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

        if not ts_filter or (ts_filter in cfn) or (ts_filter in ts['prompt'].lower()):

            if options.missing_words:

                missing = False

                t = ts['ts']
                if len(t) == 0:
                    t = ' '.join(tokenize(ts['prompt']))
                    
                for token in t.split(' '):

                    if not token in lex:
                        missing = True
                        break
                if missing:
                    edit_ts.append(ts)

            else:
                edit_ts.append(ts)

        cur_ts = 0

    if len(edit_ts) == 0:
        raise Exception ('no submissions found!')

    while True:
    
        ts = edit_ts[cur_ts]

        missing_token = paint_main(stdscr, cur_ts)

        c = stdscr.getch()
        if c == ord('q'):
            break  
   
        elif c == ord('p'):
            play_wav(ts)

        elif c == ord('1'):
            accept_ts(1, cur_ts)
            missing_token, cur_ts = goto_next_ts(cur_ts)
        elif c == ord('2'):
            if not missing_token:
                accept_ts(2, cur_ts)
                missing_token, cur_ts = goto_next_ts(cur_ts)
        elif c == ord('3'):
            if not missing_token:
                accept_ts(3, cur_ts)
                missing_token, cur_ts = goto_next_ts(cur_ts)
                    
        elif c == ord('e'):

            ts['prompt'] = utils.edit_popup(stdscr, ' Prompt ', ts['prompt'])
            ts['ts'] = ''

        elif c == ord('a'):

            if prompt_token_idx < len(prompt_tokens):
                if len(ts['prompt']) > 0:
                    ts['prompt'] += ' '
                ts['prompt'] +=  prompt_tokens[prompt_token_idx]
                ts['ts'] = ''
                prompt_token_idx += 1

        elif c == ord('s'):

            if prompt_token_idx < len(prompt_tokens):
                prompt_token_idx += 1

        elif c == ord('b'):

            if prompt_token_idx >0:

                prompt_token_idx -= 1

                cur_tokens = tokenize(ts['ts'])

                if len(cur_tokens)>1:
                    ts['prompt'] = ' '.join(cur_tokens[0:len(cur_tokens)-1])
                else:
                    ts['prompt'] = ''
                ts['ts'] = ''

        elif c == ord('t'):

            ts['ts'] = utils.edit_popup(stdscr, ' Transcript ', ts['ts'])

        elif c == ord('l'):
            if missing_token:
                t = missing_token
            else:
                t = tokenize(ts['ts'])[0]

            lex_edit(t)


    #
    # fini
    #

    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()

    transcripts.save()
    print "new transcripts saved."
    print

    lex.save()
    print "new lexicon saved."
    print

except:
    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()

    print u"*** ERROR: Unexpected error:", sys.exc_info()[0]
    traceback.print_exc()
    #raise

