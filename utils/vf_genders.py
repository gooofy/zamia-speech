#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2017 Guenter Bartsch
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
# extract speaker gender information from voxforge submission README files
#
# WARNING: this is a very crude script, use with care!
#

import argparse
import os
import codecs
import re
import logging

from optparse import OptionParser
from nltools  import misc

PROC_TITLE='vf_gender'

VFDIR  = '/home/bofh/projects/ai/data/speech/en/voxforge/audio'

ENTRY_MAP = {
             'Gender: Male'       : 'm',
             'Gender: Female'     : 'f',
             'Gender: [male];'    : 'm',
             'Gender: [female];'  : 'f',
             'Gender: male'       : 'm',
             'Gender: female'     : 'f',
             'Gender: unknown'    : 'm',
             'Gender: male;'      : 'm',
             'Gender: female;'    : 'f',
             'Gender: Weiblich'   : 'f',
             'Gender: Masculino'  : 'm',
            }

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


#
# main
#

gender_map = {} # speaker -> gender

for submission in os.listdir (VFDIR):

    logging.debug('submission: %s' % submission)

    parts = submission.split('-')
    if len(parts)<2:
        continue
    speaker = parts[0]
    if speaker in gender_map:
        continue

    try:
        with open('%s/%s/etc/README' % (VFDIR, submission), 'r') as readmef:
            for line in readmef:
                if not 'Gender:' in line:
                    continue

                entry = line.strip()
                if not entry in ENTRY_MAP:
                    logging.error ('failed to parse entry: %s' % repr(entry))
                    sys.exit(0) 

                g = ENTRY_MAP[entry]
                gender_map[speaker] = g
                logging.debug('gender for %s: %s' % (speaker, g))
                break
    except:
        pass

for speaker in sorted(gender_map):

    print '%s %s' % (speaker, gender_map[speaker])

