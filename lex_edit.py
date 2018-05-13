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

#
# lex-edit loop component, intended to be embedded into other scripts
#

import sys
import os
import traceback
import logging
import readline

from nltools.tts            import TTS
from nltools.sequiturclient import sequitur_gen_ipa
from nltools.phonetics      import ipa2xsampa, xsampa2ipa
from seqif                  import SeqIf

SEQUITUR_MODEL    = 'data/models/sequitur-dict-de.ipa-latest'

class LexEdit(object):

    def __init__(self, lex):
    
        self.lex = lex

        #
        # TTS (for audio output)
        #

        self.tts = TTS ('local', 0, locale='de', voice='bits3', engine='espeak')

        #
        # sequitur interface
        #

        self.si = SeqIf(SEQUITUR_MODEL)

    def lex_gen_ipa (self, lex_base, locale, engine, voice, speak=False):

        ipas = u''
        try:

            if engine == 'sequitur':
                # ipas = sequitur_gen_ipa (SEQUITUR_MODEL, lex_base)
                ipas = self.si.g2p(lex_base)
            
            else:
                self.tts.locale = locale
                self.tts.engine = engine
                self.tts.voice  = voice
                ipas = self.tts.gen_ipa (lex_base)

            if speak:
                self.tts.locale = 'de'
                self.tts.engine = 'mary'
                self.tts.voice  = 'dfki-pavoque-neutral-hsmm'
                self.tts.say_ipa(ipas, async=True)

        except:
            logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

        return ipas

    def edit(self, lex_token):

        lex_base  = lex_token.split('_')[0]

        if lex_token in self.lex:
            lex_entry = lex[lex_token]

        else:
            ipas = self.lex_gen_ipa(lex_base, 'de', 'sequitur', 'de')
            lex_entry = {'ipa': ipas}
            self.lex[lex_token] = lex_entry

        ipas = lex_entry['ipa']

        lex_gen = {}

        lex_gen['de-mary']     = self.lex_gen_ipa(lex_base, 'de', 'mary',     'bits3')
        lex_gen['de-espeak']   = self.lex_gen_ipa(lex_base, 'de', 'espeak',   'de')
        lex_gen['de-sequitur'] = self.lex_gen_ipa(lex_base, 'de', 'sequitur', 'de')

        try:
            self.tts.locale ='de'
            self.tts.engine ='mary'
            self.tts.voice  ='dfki-pavoque-neutral-hsmm'
            self.tts.say_ipa(ipas, async=True)
        except:
            logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

        while True:

            print
            print u"Token       : %s" % lex_token
            print u"IPA         : %s" % lex_entry['ipa']
            print

            for engine in sorted(lex_gen):
                print u"%-11s : %s" % (engine, lex_gen[engine])
            print

            if lex_token in self.lex:
                m = self.lex.get_multi(lex_token)
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
                    lex_entry['ipa'] = self.lex_gen_ipa (lex_base, 'de', 'mary', 'bits3', True)

                # generate de-espeak
                elif resp.lower() == 'h':
                    lex_entry['ipa'] = self.lex_gen_ipa (lex_base, 'de', 'espeak', 'de', True)
                    
                # generate en-mary 
                elif resp.lower() == 'l':
                    
                    self.tts.locale ='en-US'
                    self.tts.engine ='mary'
                    self.tts.voice  ='cmu-rms-hsmm'

                    ipas = self.tts.gen_ipa (lex_base)
                    self.tts.say_ipa(ipas, async=True)
                    lex_entry['ipa'] = ipas

                # generate fr-mary 
                elif resp.lower() == 'k':
                    
                    self.tts.locale ='fr'
                    self.tts.engine ='mary'
                    self.tts.voice  ='upmc-pierre-hsmm'

                    ipas = self.tts.gen_ipa (lex_base)
                    self.tts.say_ipa(ipas, async=True)
                    lex_entry['ipa'] = ipas

                # generate de-sequitur
                elif resp.lower() == 'j':
                    lex_entry['ipa'] = self.lex_gen_ipa (lex_base, 'de', 'sequitur', 'de', True)
                    
                # speak de mary unitsel 
                elif resp.lower() == 'p':
            
                    if len(lex_entry['ipa']) == 0:
                        continue
            
                    ipas = lex_entry['ipa']

                    self.tts.locale ='de'
                    self.tts.engine ='mary'
                    self.tts.voice  ='bits3'

                    self.tts.say_ipa(ipas, async=True)

                # speak de mary hsmm
                elif resp.lower() == 'o':
            
                    if len(lex_entry['ipa']) == 0:
                        continue
            
                    ipas = lex_entry['ipa']

                    self.tts.locale = 'de'
                    self.tts.engine = 'mary'
                    self.tts.voice  = 'dfki-pavoque-neutral-hsmm'

                    self.tts.say_ipa(ipas, async=True)

                # speak fr mary hsmm
                elif resp.lower() == 'i':
           
                    if len(lex_entry['ipa']) == 0:
                        continue
            
                    ipas = lex_entry['ipa']

                    self.tts.locale ='fr'
                    self.tts.engine ='mary'
                    self.tts.voice  ='upmc-pierre-hsmm'

                    self.tts.say_ipa(ipas, async=True)
           
                # speak en mary hsmm
                elif resp.lower() == 'u':
            
                    ipas = lex_entry['ipa']

                    self.tts.locale = 'en-US'
                    self.tts.engine = 'mary'
                    self.tts.voice  = 'cmu-rms-hsmm'

                    self.tts.say_ipa(ipas, async=True)
           
                # edit XS
                elif resp.lower() == 'e':
            
                    ipas = lex_entry['ipa']

                    xs = ipa2xsampa (lex_token, ipas, stress_to_vowels=False)
                    readline.add_history(xs)
                    xs = raw_input(xs + '> ')

                    ipas = xsampa2ipa (lex_token, xs)
        
                    lex_entry['ipa'] = ipas

            except:
                logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

        self.lex.save()
        print "new lexicon saved."
        print



