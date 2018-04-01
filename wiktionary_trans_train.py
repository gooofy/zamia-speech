#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Guenter Bartsch
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
# train a seq2seq model that translates wiktionary hyphenated word + IPA into our IPA style
#
# code based on https://github.com/keras-team/keras/blob/master/examples/lstm_seq2seq.py
#

import os
import sys
import string
import codecs
import logging

from optparse           import OptionParser

from nltools            import misc
from speech_lexicon     import Lexicon
from wiktionary_model   import WiktionarySeq2Seq

PROC_TITLE      = 'wiktionary_trans_train'
DICTFN          = 'data/dst/speech/de/dict_wiktionary_de.txt'

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# load config, set up global variables
#

config = misc.load_config ('.speechrc')

wikfn  = config.get("speech", "wiktionary_de")

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

#
# load wiktionary
#

print "loading wiktionary..."
wiktionary = {}
with codecs.open(DICTFN, 'r', 'utf8') as dictf:
    for line in dictf:
        parts = line.strip().split(';')
        if len(parts) != 2:
            print "Failed to parse line %s" % line.strip()
            continue

        word  = parts[0]
        ipa   = parts[1]
        token = word.replace(u"·", u"").lower()

        wiktionary[token] = (word, ipa)

print "loading wiktionary... done. %d entries." % len(wiktionary)

#
# extract training data
#

num_missing = 0
num_found   = 0

words        = []
ipas         = []
target_ipas  = []

for token in lex:
    if not token in wiktionary:
        # print u"Missing in wiktionary: %s" % token
        num_missing += 1
    else:
        num_found += 1

        word = wiktionary[token][0].lower()
        ipa  = wiktionary[token][1]

        target_text = lex[token]['ipa']

        words.append(word)
        ipas.append(ipa)
        target_ipas.append(target_text)

print "wiktionary vs dict: %d found, %d missing" % (num_found, num_missing)

wiktionary_model = WiktionarySeq2Seq('base_256')

wiktionary_model.train (words, ipas, target_ipas)

