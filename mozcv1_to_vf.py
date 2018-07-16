#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 by Marc Puels
# Copyright 2016 by G.Bartsch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# convert mozilla common speech to voxforge-style packages
#

import sys
import os
import codecs
import traceback
import logging
import csv

from optparse               import OptionParser
from nltools                import misc

PROC_TITLE        = 'moz_cv1_to_vf'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options]")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config ('.speechrc')
speech_arc     = config.get("speech", "speech_arc")
speech_corpora = config.get("speech", "speech_corpora")

#
# convert mp3 to 16khz mono wav, create one dir per utt
# (since we have no speaker information)
#

for csvfn in ['cv-valid-test.csv', 'cv-valid-train.csv', 'cv-valid-dev.csv']:

    with codecs.open('%s/cv_corpus_v1/%s' % (speech_arc, csvfn), 'r', 'utf8') as csvfile:
        r = csv.reader(csvfile, delimiter=',', quotechar='|')
        first = True
        for row in r:
            if first:
                first = False
                continue
            print ', '.join(row)
         
            uttid = wavfn = row[0].replace('/', '-').replace('.mp3', '')
            spk = uttid

            misc.mkdirs('%s/cv_corpus_v1/%s-v1/etc' % (speech_corpora, spk))
            misc.mkdirs('%s/cv_corpus_v1/%s-v1/wav' % (speech_corpora, spk))

            with codecs.open ('%s/cv_corpus_v1/%s-v1/etc/prompts-original' % (speech_corpora, spk), 'a', 'utf8') as promptsf:
                promptsf.write('%s %s\n' % (uttid, row[1]))

            cmd = 'rm -f tmp/foo.wav'
            os.system(cmd)
 
            cmd = 'ffmpeg -i %s/cv_corpus_v1/%s tmp/foo.wav' % (speech_arc, row[0])
            print cmd
            os.system(cmd)

            wavfn = '%s/cv_corpus_v1/%s-v1/wav/%s.wav' % (speech_corpora, spk, uttid)

            cmd = 'sox tmp/foo.wav -r 16000 -c 1 -b 16 %s' % wavfn
            print cmd
            os.system(cmd)

