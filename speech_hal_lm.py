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
# generate language model from HAL-Prolog transcripts
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
from speech_lexicon import ipa2xsampa, xsampa2ipa, xsampa2xarpabet, Lexicon
from speech_tokenizer import tokenize

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

WORKDIR = 'data/dst/lm'



#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)


#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

#
# read transcripts
#

all_tokens = set()

with codecs.open('%s/hal.txt' % WORKDIR, 'w', 'utf8') as allf:

    for tsfn in os.listdir('data/dst'):

        if not tsfn.endswith('.ts'):
            continue

        with codecs.open('data/dst/%s' % tsfn, 'r', 'utf8') as tsf:

            for line in tsf:

                tokens = tokenize(line)

                for token in tokens:
                    all_tokens.add(token)

                allf.write (u'<s> %s </s>\n' % ' '.join(tokens))

#
# wlist, dictionary
#

with codecs.open('%s/hal.vocab' % WORKDIR, 'w', 'utf8') as vocabf, \
     codecs.open('%s/hal.dic' % WORKDIR, 'w', 'utf8') as dicf:

    vocabf.write('</s>\n')
    vocabf.write('<s>\n')

    for token in sorted(all_tokens):
        vocabf.write(u'%s\n' % token)

        ipa = lex[token]['ipa']

        xs  = ipa2xsampa(token, ipa)
        xa  = xsampa2xarpabet(token, xs)
        dicf.write(u'%s %s\n' % (token, xa))

    
#
# generate sphinx lm
#

os.system('text2idngram -vocab %s/hal.vocab -idngram %s/hal.idngram < %s/hal.txt' % (WORKDIR, WORKDIR, WORKDIR))
os.system('idngram2lm -calc_mem -vocab_type 0 -idngram %s/hal.idngram -vocab %s/hal.vocab -arpa %s/hal.arpa' % (WORKDIR, WORKDIR, WORKDIR))
os.system('sphinx_lm_convert -i %s/hal.arpa -o %s/hal.lm.DMP' % (WORKDIR, WORKDIR))

