#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017, 2018 Guenter Bartsch
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
# export lexicon for sequitur model training
#

import os
import sys
import logging
import codecs
import traceback
import random

from optparse           import OptionParser
from nltools            import misc
from nltools.phonetics  import ipa2xsampa

from speech_lexicon     import Lexicon

DEFAULT_DICT='dict-de.ipa'

#
# init terminal
#

misc.init_app ('speech_sequitur_export')

#
# commandline
#

parser = OptionParser("usage: %prog [options] ")

parser.add_option ("-d", "--dict", dest="dict_name", type = "str", default=DEFAULT_DICT,
                   help="dict to export (default: %s)" % DEFAULT_DICT)
parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="verbose output")
parser.add_option ("-r", "--train-ratio", type="float", dest="ratio", default=0.9,
                   help="ratio of train words (0.0-1.0)")

(options, args) = parser.parse_args()

if options.ratio <= 0.0 or options.ratio >= 1.0:
    logging.error("Invalid ratio %f, valid values are between 0.0 and 1.0 exclusive" % options.ratio)
    sys.exit(1)

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
dict_name = options.dict_name
workdir = 'data/dst/dict-models/%s/sequitur' % dict_name


#
# load lexicon
#

logging.info("loading lexicon...")
lex = Lexicon(file_name=dict_name)
logging.info("loading lexicon...done.")

#
# export
#

misc.mkdirs(workdir)

with codecs.open('%s/train.lex' % workdir, 'w', 'utf8') as trainf, \
     codecs.open('%s/test.lex'  % workdir, 'w', 'utf8') as testf, \
     codecs.open('%s/all.lex'  % workdir, 'w', 'utf8') as allf :

    cnt = 0

    for word in lex:

        ipa = lex[word]['ipa']

        xs = ipa2xsampa (word, ipa, spaces=True, stress_to_vowels=False)

        if options.ratio < random.random():
            testf.write (u'%s %s\n' % (word, xs))
        else:
            trainf.write (u'%s %s\n' % (word, xs))
        allf.write (u'%s %s\n' % (word, xs))

        cnt += 1

logging.info('sequitur workdir %s done.' % workdir)

