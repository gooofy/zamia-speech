#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016, 2017 Guenter Bartsch
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
# apply review-result.csv file to transcripts
#

import os
import sys
import logging
import readline
import atexit
import traceback

from time               import time
from optparse           import OptionParser
from StringIO           import StringIO

from nltools            import misc
from nltools.phonetics  import ipa2xsampa
from nltools.tokenizer  import tokenize

from speech_lexicon     import Lexicon
from speech_transcripts import Transcripts

#
# init 
#

misc.init_app ('apply_reviews')

config = misc.load_config ('.speechrc')

#
# command line
#

parser = OptionParser("usage: %prog foo.csv [bar.csv ...])")

parser.add_option ("-f", "--force", action="store_true", dest="force", 
                   help="force: apply quality rating also on already reviewed entries")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                  help="language (default: de)")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

(options, args) = parser.parse_args()

if len(args)<1:
    parser.print_help()
    sys.exit(1)

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# load lexicon, transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=options.lang)
logging.info("loading transcripts...done.")

#
# main
#

cnt       = 0

for csvfn in args:

    logging.info ("applying results from %s ..." % csvfn)

    with open(csvfn, 'r') as csvf:

        for line in csvf:
            parts = line.strip().split(';')

            if len(parts) != 2:
                logging.error ('failed to parse line:' % line)
                sys.exit(1)

            utt_id = parts[0]
            quality = int(parts[1])

            if transcripts[utt_id]['quality'] != 0:
                if not force:
                    logging.warn ('skipping %s because it is already rated.' % utt_id)
                    continue
           
            transcripts[utt_id]['quality'] = quality
            transcripts[utt_id]['ts']      = u' '.join(tokenize(transcripts[utt_id]['prompt'], lang=options.lang))

            cnt += 1

logging.info ('results applied to %d transcripts.' % cnt)

logging.info("saving transcripts...")
transcripts.save()
logging.info("saving transcripts...done.")

