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
# train a sequitur model that translates wiktionary IPA into our IPA style
#

import os
import sys
import string
import codecs
import logging

from optparse           import OptionParser

from nltools            import misc
from nltools.phonetics  import ipa2xsampa
from speech_lexicon     import Lexicon

PROC_TITLE      = 'wiktionary_sequitur_train'
DICTFN          = 'data/dst/speech/de/dict_wiktionary_de.txt'
WORKDIR         = 'data/dst/speech/de/wiktionary_sequitur'

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options]")

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

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon('dict-de.ipa')
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
# export training data for sequitur
#

os.system("rm -rf %s" % WORKDIR)
misc.mkdirs(WORKDIR)

num_missing = 0
num_found   = 0

with codecs.open('%s/train.lex' % WORKDIR, 'w', 'utf8') as trainf, \
     codecs.open('%s/test.lex'  % WORKDIR, 'w', 'utf8') as testf, \
     codecs.open('%s/all.lex'   % WORKDIR, 'w', 'utf8') as allf :

    cnt = 0

    for token in lex:
        if not token in wiktionary:
            # print u"Missing in wiktionary: %s" % token
            num_missing += 1
        else:
            num_found += 1

            source_ipa = wiktionary[token][1]
            target_ipa = lex[token]['ipa'].replace(u'-', u'')

            target_xs = ipa2xsampa (token, target_ipa, spaces=True, stress_to_vowels=False)

            if cnt % 10 == 0:
                testf.write (u'%s %s\n' % (source_ipa, target_xs))
            else:
                trainf.write (u'%s %s\n' % (source_ipa, target_xs))
            allf.write (u'%s %s\n' % (source_ipa, target_xs))

            cnt += 1

logging.info('sequitur workdir %s done. %d entries.' % (WORKDIR, cnt))


