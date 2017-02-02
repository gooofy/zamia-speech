#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016 Guenter Bartsch
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
# crude sequitur g2p interface, used in LexEdit
#

import os
import sys
import re
import logging
import codecs

import utils

from speech_lexicon import xsampa2ipa

LANG = 'de'

MODELFN = 'data/models/sequitur-voxforge-%s-r20161117' % LANG
TMPFN   = '/tmp/sequitur_words_%s.txt' % LANG

def sequitur_gen_ipa(word):

    with codecs.open(TMPFN, 'w', 'utf8') as f:
        f.write(u'%s\n' % word)

    res = utils.run_command(['g2p.py', '--model', MODELFN, '--apply', TMPFN])

    # print repr(res)

    ipa = u''

    for l in res:

        line = l.strip()

        # print 'LINE', line

        if 'stack usage:' in line:
            continue

        if word in line.decode('utf8'):
            parts = line.split('\t')

            if len(parts) < 2:
                continue

            xs = parts[1]
            # print 'XS', xs
       
            ipa = xsampa2ipa(word, xs)


    return ipa

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    #
    # init terminal
    #

    reload(sys)
    sys.setdefaultencoding('utf-8')
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    #
    # test sequitur
    #

    ipa = sequitur_gen_ipa('hauptbahnhof')

    print u'got ipa from sequitur: %s' % ipa

