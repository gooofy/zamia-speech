#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017 Guenter Bartsch
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
# compare lex entries to what eSpeak ng generates and export entries for differing words
#

import os
import sys
import logging
import traceback
import locale
import codecs

from optparse           import OptionParser
from speech_lexicon     import Lexicon
from nltools            import misc
from espeakng           import ESpeakNG
from nltools.phonetics  import ipa2xsampa, xsampa2ipa, espeak2ipa, ipa2espeak

# DEBUG_LIMIT = 0
DEBUG_LIMIT = 1000

PROC_TITLE = 'speech_lex_export_espeak'

#
# init
#

misc.init_app(PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options])")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

#
# load lexicon
#

logging.info ( "loading lexicon...")
lex = Lexicon(file_name=options.lang)
logging.info ( "loading lexicon...done.")

#
# espeak
#

if options.lang == 'en':
    esng = ESpeakNG(voice='english-us')
elif options.lang =='de':
    esng = ESpeakNG(voice='de')
else:
    raise Exception ('no support for language %s yet.' % options.lang)

#
# main loop
#

cnt     = 0
cnt_new = 0

outfn   = '%s_extra' % options.lang

with codecs.open (outfn, 'w', 'utf8') as outf:

    for word in lex:

        cnt += 1

        if '_' in word:
            continue

        entry = lex[word]
        ipa1 = entry['ipa'].replace(u'-',u'').replace(u'ʔ',u'')
        es1  = ipa2espeak (word, ipa1, stress_to_vowels=True)
        es2  = esng.g2p (word)
        ipa2 = espeak2ipa (word, es2)
        es2  = ipa2espeak (word, ipa2, stress_to_vowels=True)

        if es1 == es2:
            logging.info (u'%6d/%6d [      MATCH] %s' % (cnt, len(lex), word))
            continue

        cnt_new += 1
        logging.info (u'%6d/%6d [new: %6d] %s -> %s : %s' % (cnt, len(lex), cnt_new, word, es1, es2))

        outf.write(u'%s\t%s\n' % (word, es1))

        if DEBUG_LIMIT and cnt_new >= DEBUG_LIMIT:
            break

logging.info ('%d entries written to %s .' % (cnt_new, outfn))


