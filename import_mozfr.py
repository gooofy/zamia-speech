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

PROC_TITLE        = 'moz_fr_to_vf'
DEFAULT_NUM_CPUS  = 12

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-n", "--num-cpus", dest="num_cpus", type="int", default=DEFAULT_NUM_CPUS,
                   help="number of cpus to use in parallel, default: %d" % DEFAULT_NUM_CPUS)

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
# convert mp3 to wav, create one dir per utt
# (since we have no speaker information)
#

uttids = set()

cnt = 0
with open('tmp/run_parallel.sh', 'w') as scriptf:
    with codecs.open('%s/cv_fr/validated.tsv' % speech_arc, 'r', 'utf8') as csvfile:
        r = csv.reader(csvfile, delimiter='\t', quotechar='|')
        first = True
        for row in r:
            if first:
                first = False
                continue
            # print ', '.join(row)
         
            uttid = row[1].replace('.mp3', '')[:12]
            spk = uttid

            if uttid in uttids:
                logging.error('uttid %s ist not unique!' % uttid)
                continue
            uttids.add(uttid)

            misc.mkdirs('%s/cv_fr/%s-fr/etc' % (speech_corpora, spk))
            misc.mkdirs('%s/cv_fr/%s-fr/wav' % (speech_corpora, spk))

            with codecs.open ('%s/cv_fr/%s-fr/etc/prompts-original' % (speech_corpora, spk), 'a', 'utf8') as promptsf:
                promptsf.write('%s %s\n' % (uttid, row[2]))

            wavfn = '%s/cv_fr/%s-fr/wav/%s.wav' % (speech_corpora, spk, uttid)
            cmd = 'ffmpeg -i %s/cv_fr/clips/%s.mp3 %s' % (speech_arc, row[1], wavfn)
            logging.info('%6d %s' % (cnt, wavfn))
            scriptf.write('echo %6d %s &\n' % (cnt, wavfn))
            scriptf.write('%s &\n' % cmd)

            cnt += 1
            if (cnt % options.num_cpus) == 0:
                scriptf.write('wait\n')

cmd = "bash tmp/run_parallel.sh"
print cmd
# os.system(cmd)


