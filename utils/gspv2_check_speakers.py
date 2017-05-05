#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 by G.Bartsch
# Copyright 2015 Language Technology, Technische Universitaet Darmstadt (author: Benjamin Milde)
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

import argparse
import os
import codecs
import re
from bs4 import BeautifulSoup
import errno
import shutil

#
# crude consistency check script for gspv2
#

DESTDIR='/home/bofh/projects/ai/data/speech/de/gspv2'

smap = {}

for folder in ['train','test','dev']:
# for folder in ['dev', 'test']:

    print
    print folder
    print

    speakers = set()

    destdir = '%s/%s' % (DESTDIR, folder)

    num_files = 0
    for f in os.listdir(folder):
        if f.endswith('xml'):
            num_files += 1

    cnt_files = 0

    for f in os.listdir(folder):
        if f.endswith('xml'):

            cnt_files += 1
            
            with codecs.open(folder + '/' + f,'r','utf-8') as xmlfile:
                #remove urls
                text = xmlfile.read()
                soup = BeautifulSoup(text)
                sentence = (soup.recording.sentence.string).strip()
                cleaned_sentence = (soup.recording.cleaned_sentence.string).strip()
                sentence_id = int((soup.recording.sentence_id.string).strip())

                speaker_id = (soup.recording.speaker_id.string).strip()

                if not speaker_id in speakers:
                    speakers.add(speaker_id)
                    print speaker_id


    smap[folder] = speakers


for f1 in smap:
    for f2 in smap:
        if f1 == f2:
            continue
        for speaker in smap[f1]:
            if speaker in smap[f2]:
                print "*** ERROR: speaker %s is in dir %s and %s!" % (speaker, f1, f2)


