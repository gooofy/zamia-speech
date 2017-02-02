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
# interactive curses lexicon editor
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

#
# Lex Editor
#

TOKENIZER_ERRORS='data/src/speech/de/tokenizer_errors.txt'

def lex_paint_main():

    global stdscr, lex_token, lex, lex_entry, lex_tokens, lex_cur_token, lex_gen

    stdscr.clear()

    my, mx = stdscr.getmaxyx()

    for x in range(mx):
        stdscr.insstr(   0, x, ' ', curses.A_REVERSE)
        stdscr.insstr(my-2, x, ' ', curses.A_REVERSE)
        stdscr.insstr(my-1, x, ' ', curses.A_REVERSE)

    stdscr.insstr(0,     0, "%3d/%3d" % (lex_cur_token, len(lex_tokens)), curses.A_REVERSE )
    stdscr.insstr(0, mx-15, "Lexicon Editor", curses.A_REVERSE )

    stdscr.insstr(4, 2, ("Token       : %s" % lex_token).encode('utf8'))
    stdscr.insstr(5, 2, ("IPA         : %s" % lex_entry['ipa']).encode('utf8'))

    cy = 6
    for engine in sorted(lex_gen):
        stdscr.insstr(cy, 2, ("%-11s : %s" % (engine, lex_gen[engine])).encode('utf8'))
        cy += 1

    cy += 1

    if lex_token in lex:

        m = lex.get_multi(lex_token)
        for k in m:
            stdscr.insstr(cy, 4, ("%s [%s]" % (k, m[k]['ipa'])).encode('utf8'))
            cy += 1

    else:
        stdscr.insstr(10, 4, "NEW TOKEN")

    stdscr.insstr(my-2, 0, "SPEAK  P:de-unitsel  O:de-hsmm                   I:fr-hsmm   U:en-hsmm", curses.A_REVERSE )
    stdscr.insstr(my-1, 0, "GEN    G:de-mary     H:de-espeak  J:de-sequitur  K:fr-mary   L:en-mary", curses.A_REVERSE )
    stdscr.insstr(my-2, mx-40, "                                 N:Next ", curses.A_REVERSE )
    stdscr.insstr(my-1, mx-40, " R:remove  E:Edit  T:Token       Q:Quit ", curses.A_REVERSE )
    stdscr.refresh()

def lex_gen_ipa (locale, engine, voice, speak=False):

    global tts

    if engine == 'sequitur':
        ipas = sequitur_gen_ipa (lex_base)
    
    else:
        tts.set_locale (locale)
        tts.set_engine (engine)
        tts.set_voice  (voice)
        ipas = tts.gen_ipa (lex_base)

    if speak:
        tts.set_locale ('de')
        tts.set_engine ('mary')
        tts.set_voice  ('dfki-pavoque-neutral-hsmm')
        tts.say_ipa(ipas)

    return ipas


def lex_set_token(token):

    global lex, lex_token, lex_entry, lex_base, lex_gen

    lex_token = token
    lex_base  = token.split('_')[0]

    if lex_token in lex:

        lex_entry = lex[lex_token]

    else:

        ipas = lex_gen_ipa('de', 'sequitur', 'de')
        lex_entry = {'ipa': ipas}
        lex[lex_token] = lex_entry


    ipas = lex_entry['ipa']

    tts.set_locale ('de')
    tts.set_engine ('mary')
    tts.set_voice ('dfki-pavoque-neutral-hsmm')
    tts.say_ipa(ipas)

    lex_gen['de-mary']     = lex_gen_ipa('de', 'mary',     'bits3')
    lex_gen['de-espeak']   = lex_gen_ipa('de', 'espeak',   'de')
    lex_gen['de-sequitur'] = lex_gen_ipa('de', 'sequitur', 'de')


logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

#
# command line
#

parser = OptionParser("usage: %prog [options] tokens ...)")

(options, args) = parser.parse_args()

if len(args)<1:
    parser.print_usage()
    print
    sys.exit(1)

lex_tokens    = map(lambda x: x.decode('utf8'), args)

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

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

host        = config.get('tts', 'host')
port        = int(config.get('tts', 'port'))

#
# TTS Client
#

tts = TTSClient (host, port, locale='de', voice='bits3')

#
# main 
#

try:

    lex_gen = {}
    lex_cur_token = 0
    lex_set_token (lex_tokens[lex_cur_token])

    while True:
    
        lex_paint_main()
    
        c = stdscr.getch()

        # quit
        if c == ord('q'):
            break  
    
        elif c == ord('n'):
            lex_cur_token = (lex_cur_token + 1) % len(lex_tokens)
            lex_set_token (lex_tokens[lex_cur_token])
   
        # remove wrong entry 
        elif c == ord('r'):

            wrong_token = lex_tokens[lex_cur_token]

            lex_tokens.remove(wrong_token)
            lex.remove(wrong_token)

            with codecs.open(TOKENIZER_ERRORS, 'a', 'utf8') as f:
                f.write('%s\n' % wrong_token)

            lex_cur_token = lex_cur_token % len(lex_tokens)
            lex_set_token (lex_tokens[lex_cur_token])
    
        # generate de-mary
        elif c == ord('g'):
            lex_entry['ipa'] = lex_gen_ipa ('de', 'mary', 'bits3', True)

        # generate de-espeak
        elif c == ord('h'):
            lex_entry['ipa'] = lex_gen_ipa ('de', 'espeak', 'de', True)
            
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
            lex_entry['ipa'] = lex_gen_ipa ('de', 'sequitur', 'de', True)
            
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
            tts.set_voice ('upmc-pierre-hsmm')

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

                

    #
    # fini
    #

    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()

    lex.save()
    print "new lexicon saved."
    print

except:
    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()

    print u"*** ERROR: Unexpected error:", sys.exc_info()[0]
    traceback.print_exc()

