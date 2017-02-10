#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016 Guenter Bartsch
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

import sys
import re
import unittest
import codecs

from nltools.phonetics import _normalize, IPA_normalization

#
# Lexicon load/save abstraction
#

class Lexicon(object):

    def __init__(self, lang='de'):

        self.lang       = lang
        self.dictionary = {}
        self.multidict  = {}

        with open('data/src/speech/%s/dict.ipa' % self.lang, 'r') as f:

            while True:

                line = f.readline().rstrip().decode('utf8')

                if not line:
                    break

                parts = line.split(';')
                # print repr(parts)

                ipas = _normalize (parts[1],  IPA_normalization)

                k = parts[0]
                v = {'ipa': ipas}

                self.dictionary[k] = v
                b = k.split('_')[0]
                if not b in self.multidict:
                    self.multidict[b] = {}
                self.multidict[b][k] = v


    def __len__(self):
        return len(self.dictionary)

    def __getitem__(self, key):
        return self.dictionary[key]

    def __iter__(self):
        return iter(sorted(self.dictionary))

    def __setitem__(self, k, v):
        self.dictionary[k] = v
        b = k.split('_')[0]
        if not b in self.multidict:
            self.multidict[b] = {}
        self.multidict[b][k] = v

    def __contains__(self, key):
        return key in self.dictionary

    def get_multi(self, k):
        b = k.split('_')[0]
        return self.multidict[b]

    def save(self):
        with codecs.open('data/src/speech/%s/dict.ipa' % self.lang, 'w', 'utf8') as f:
            for w in sorted(self.dictionary):
                entry = self.dictionary[w]
                f.write(u"%s;%s\n" % (w, entry['ipa']))

    def remove(self, key):
        del self.dictionary[key]

