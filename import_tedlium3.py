#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 by G.Bartsch
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
# convert TED-LIUM v3 to voxforge-style packages
#

import sys
import os
import codecs
import traceback
import logging
import csv

from optparse               import OptionParser
from nltools                import misc

PROC_TITLE        = 'import_tedlium3'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
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
# create destination dir
#

dest_dir = '%s/tedlium3' % speech_corpora
cmd = 'rm -rf %s' % dest_dir
os.system(cmd)
logging.info(cmd)
cmd = 'mkdir -p %s' % dest_dir
logging.info(cmd)
os.system(cmd)

#
# create wav files
#

tedlium_dir = '%s/TEDLIUM_release-3' % speech_arc

ddict = {}

for stmfn in os.listdir('%s/data/stm' % tedlium_dir):

    for line in codecs.open('%s/data/stm/%s' % (tedlium_dir, stmfn), 'r', 'utf8'):
        parts = line.strip().split(' ')

        speaker = parts[2].replace('_','-')
        tstart  = float(parts[3])
        tend    = float(parts[4])

        ts = u''
        for lex in parts[6:]:
            if u'<unk>' in lex:
                continue
            if lex.startswith(u"'"):
                ts = ts + lex
                continue
            if ts:
                ts = ts + u' ' + lex
            else:
                ts = lex

        print speaker, tstart, tend, ts

        speakerdir = '%s/%s-1' % (dest_dir, speaker)

        if not (speaker in ddict):
            ddict[speaker] = 0
            misc.mkdirs('%s/etc' % speakerdir)
            misc.mkdirs('%s/wav' % speakerdir)
        
        audiobn = '%09d' % ddict[speaker]
        ddict[speaker] += 1

        with codecs.open('%s/etc/prompts-original' % speakerdir, 'a', 'utf8') as promptsfn:
            promptsfn.write(u'%s %s\n' % (audiobn, ts))

        cmd = 'sph2pipe -t %f:%f %s/data/sph/%s %s/wav/%s.wav' % (tstart, tend, tedlium_dir, stmfn.replace('.stm','.sph'), speakerdir, audiobn)
        logging.info(cmd)
        os.system(cmd)
        
