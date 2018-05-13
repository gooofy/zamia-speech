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
# sequitur g2p interface
#

import sys
import os
import traceback
import logging
import readline

from nltools.tts            import TTS
from nltools.sequiturclient import sequitur_gen_ipa
from nltools.phonetics      import ipa2xsampa, xsampa2ipa

import SequiturTool
from sequitur import Translator

SEQUITUR_MODEL    = 'data/models/sequitur-dict-de.ipa-latest'

class SeqOptionsObject(object):
    pass

def loadG2PSample(fname):
    if fname == '-':
        sample = loadPlainSample(fname)
    else:
        firstLine = gOpenIn(fname, defaultEncoding).readline()
        if firstLine.startswith('<?xml'):
            sample = [ (tuple(orth), tuple(phon))
                       for orth, phon in loadBlissLexicon(fname) ]
        else:
            sample = loadPlainSample(fname)
    return sample

class SeqIf(object):

    def __init__(self, modelfn=SEQUITUR_MODEL):

        options = SeqOptionsObject()
        options.resume_from_checkpoint = False
        options.modelFile              = modelfn
        options.shouldRampUp           = False
        options.trainSample            = None
        options.shouldTranspose        = False
        options.newModelFile           = None
        options.shouldSelfTest         = False

        self.model = SequiturTool.procureModel(options, loadG2PSample, log=sys.stdout)

        self.translator = Translator(self.model)

    def g2p(self, word):

        res = self.translator(word)

        xs = u' '.join(res)
        ipa = xsampa2ipa(word, xs)

        return ipa

if __name__ == '__main__':

    si = SeqIf()

    ipa = si.g2p(u'überhaupt')

    print ipa
