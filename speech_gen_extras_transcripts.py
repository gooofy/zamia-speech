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
# reconstruct prompts-original where it is missing in extras-dir
#

import os
import sys
import logging
import traceback
import codecs

from optparse           import OptionParser

from nltools            import misc
from speech_transcripts import Transcripts

#
# init 
#

misc.init_app ('speech_gen_extras_transcript')

config = misc.load_config ('.speechrc')

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

#
# commandline
#

parser = OptionParser("usage: %prog [options] ")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
           help="language (default: de)")

(options, args) = parser.parse_args()

lang = options.lang

extrasdirfn = config.get('speech', 'extrasdir_%s' % options.lang)

#
# load transcripts
#

print "loading transcripts..."
transcripts = Transcripts(lang=lang)
print "loading transcripts...done."

#
# look for missing prompts-origin, reconstruct it from transcripts
#

for dirfn in sorted(os.listdir(extrasdirfn)):

    if not os.path.isdir('%s/%s' % (extrasdirfn, dirfn)):
        continue

    promptsfn = '%s/%s/etc/prompts-original' % (extrasdirfn, dirfn)

    if os.path.exists(promptsfn):
        print "%s exists." % promptsfn
        continue

    print "reconstructing %s" % promptsfn

    misc.mkdirs('%s/%s/etc' % (extrasdirfn, dirfn))

    with codecs.open(promptsfn, 'w', 'utf8') as promptsf:

        for cfn in sorted(transcripts):

            if not cfn.startswith(dirfn):
                continue

            # de5-015 computer wann wurde city of god gedreht

            line = u"%s %s\n" % (transcripts[cfn]['audiofn'], transcripts[cfn]['prompt'])

            promptsf.write(line) 
            print line.strip()

