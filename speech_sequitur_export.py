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
# export lexicon for sequitur model training
#

import os
import sys
import logging
import codecs
import traceback

import utils
from speech_lexicon import ipa2xsampa, Lexicon

LANG    = 'de'
WORKDIR = 'data/dst/speech/%s/sequitur' % LANG

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

#
# load lexicon
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

#
# export
#

utils.mkdirs(WORKDIR)

with codecs.open('%s/train.lex' % WORKDIR, 'w', 'utf8') as trainf, \
     codecs.open('%s/test.lex'  % WORKDIR, 'w', 'utf8') as testf, \
     codecs.open('%s/all.lex'  % WORKDIR, 'w', 'utf8') as allf :

    cnt = 0

    for word in lex:

        ipa = lex[word]['ipa']

        xs = ipa2xsampa (word, ipa, spaces=True, stress_to_vowels=False)

        if cnt % 10 == 0:
            testf.write (u'%s %s\n' % (word, xs))
        else:
            trainf.write (u'%s %s\n' % (word, xs))
        allf.write (u'%s %s\n' % (word, xs))

        cnt += 1


