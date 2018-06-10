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
# extract sentences from audiobook prompts using our pre-trained punkt 
# tokenizer
#

import sys
import os
import codecs
import traceback
import logging
import pickle

from optparse               import OptionParser
from StringIO               import StringIO
from nltools                import misc
from nltools.tokenizer      import tokenize

PROC_TITLE        = 'abook-sentences'
PUNKT_PICKLEFN    = 'data/dst/tokenizers/punkt-de.pickle'
CORPORADIR        = 'data/dst/text-corpora'
LANG              = 'de'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options] foo-1.prompt [foo-2.prompt ...]")

parser.add_option("-n", "--name", dest="name", type="str", default="abook",
                  help="dataset name (default: abook)")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) < 1:
    parser.print_usage()
    sys.exit(1)

outputfn = '%s/%s.txt' % (CORPORADIR, options.name)

#
# load punkt tokenizer
#

logging.info ("loading %s ..." % PUNKT_PICKLEFN)

with open(PUNKT_PICKLEFN, mode='rb') as f:
    punkt = pickle.load(f)

#
# main
#

logging.info ("extracting sentences ...")

cnt = 0

with codecs.open(outputfn, 'w', 'utf8') as outputf:

    for inputfn in args:

        with codecs.open(inputfn, 'r', 'utf8') as inputf:

            txt = inputf.read()

            sentences = punkt.tokenize(txt, realign_boundaries=True)
            for sentence in sentences:

                s = (u' '.join(tokenize(sentence, lang=LANG))).strip()

                if not s:
                    continue

                logging.debug("sentence: %s" % s)

                outputf.write('%s\n' % s)
                cnt += 1

logging.info ('%s written, %d sentences.' % (outputfn, cnt))

