#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2019 Guenter Bartsch
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
# convert CMU dict to zamia-speech IPA format
#

import os
import sys
import codecs
import logging

from optparse           import OptionParser
from nltools            import misc
from nltools.phonetics  import xsampa2ipa
from speech_lexicon     import Lexicon
from functools          import reduce

PROC_TITLE      = 'lex_conv_cmudict'

DEBUG_LIMIT = 0
# DEBUG_LIMIT = 100

CMUDICTFN = 'data/src/dicts/dict-en-cmudict.ipa'

ALPHABET = set("abcdefghijklmnopqrstuvwxyz'")

CMU2XS = {
          "'"   : "'",
           'AA'  : 'A',
           'AE'  : '{',
           'AH'  : 'V',  ##
           'AO'  : 'O',  ##
           'AW'  : 'aU',
           'AY'  : 'aI',
           'B'   : 'b',
           'CH'  : 'tS',
           'D'   : 'd',
           'DH'  : 'D',
           'EH'  : 'E',
           'ER'  : '3',
           'EY'  : 'eI',
           'F'   : 'f',
           'G'   : 'g',
           'HH'  : 'h',
           'IH'  : 'I',
           'IY'  : 'i',
           'JH'  : 'dZ',
           'K'   : 'k',
           'L'   : 'l',
           'M'   : 'm',
           'NG'  : 'N',
           'N'   : 'n',
           'OW'  : 'oU',
           'OY'  : 'OI', ##
           'P'   : 'p',
           'R'   : 'r',
           'SH'  : 'S',
           'S'   : 's',
           'TH'  : 'T',
           'T'   : 't',
           'UH'  : 'U',
           'UW'  : 'u',
           'V'   : 'v',
           'W'   : 'w',
           'Y'   : 'j',
           'ZH'  : 'Z',
           'Z'   : 'z',
         }

#
# init
#

misc.init_app(PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %%prog [options] cmudict.dict.txt")

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

#
# load config, set up global variables
#

config = misc.load_config ('.speechrc')

#
# convert CMU dict to zamia-speech IPA format
#

lex_new = {}

with codecs.open(args[0], 'r', 'utf8') as dictf:

    for line in dictf:

        if '#' in line:
            logging.debug('comment        : %s' % line)
            line = line.split('#')[0]
            logging.debug('comment removed: %s' % line)

        parts = line.strip().split(' ')
        word = parts[0]

        alphacheck = reduce(lambda t, c: False if not t else c.lower() in ALPHABET, word, True)
        if not alphacheck:
            logging.debug(u'alphacheck failed on %s' % word)
            continue

        if word in lex_new:
            logging.debug(u'already have an entry for %s' % word)
            continue

        xs = u''

        for ph in parts[1:]:

            l = len(ph)

            stress = False
            if ph[l-1]==u'0':
                ph = ph[:l-1]
            elif ph[l-1]==u'1':
                ph = ph[:l-1]
                stress = True
            elif ph[l-1]==u'2':
                ph = ph[:l-1]
                # stress = True

            if stress:
                xs += u"'"
            xs += CMU2XS[ph] + u' '

        ipa = xsampa2ipa(word, xs)

        # logging.debug(u'%s %s %s' % (word, xs, ipa))
        logging.debug(u'%s %s' % (word, ipa))

        lex_new[word] = ipa

        if DEBUG_LIMIT and len(lex_new) >= DEBUG_LIMIT:
            logging.warn('DEBUG LIMIT REACHED!')
            break

# #
# # diff against existing dict
# #
# 
# print "loading lexicon..."
# lex = Lexicon('dict-en.ipa')
# print "loading lexicon...done."
# 
# for word in sorted(lex_new):
# 
#     if not word in lex:
#         logging.info ('new word: %s' % word)
#         continue
# 
#     ipa_old = lex[word]['ipa']
#     ipa_new = lex_new[word]
# 
#     if ipa_old != ipa_new:
#         logging.info (u'diff: %s %s vs %s' % (word, ipa_old, ipa_new))

#
# output new cmudict result
#

with codecs.open(CMUDICTFN, 'w', 'utf8') as cmudictf:

    for word in sorted(lex_new):

        ipa_new = lex_new[word]
        cmudictf.write(u'%s %s\n' % (word, ipa_new))

logging.info ('%s written.' % CMUDICTFN)

