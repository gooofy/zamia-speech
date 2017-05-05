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
# convert german-speechdata-package-v2 to voxforge-style packages
#
# WARNING: this is a very crude script, use with care!
#

DESTDIR='/home/bofh/projects/ai/data/speech/de/gspv2'

def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def copy_file (src, dst):
    # print "copying %s to %s" % (src, dst)
    shutil.copy(src, dst)


speakers = set()

with open ('gender.txt', 'w') as genderf:

    for folder in ['train','test','dev']:
    # for folder in ['dev', 'test']:

        destdir = '%s/%s' % (DESTDIR, folder)

        num_files = 0
        for f in os.listdir(folder):
            if f.endswith('xml'):
                num_files += 1

        cnt_files = 0

        for f in os.listdir(folder):
            if f.endswith('xml'):

                cnt_files += 1
                
                fbase = f[0:len(f)-4]

                with codecs.open(folder + '/' + f,'r','utf-8') as xmlfile:
                    #remove urls
                    text = xmlfile.read()
                    soup = BeautifulSoup(text)
                    sentence = (soup.recording.sentence.string).strip()
                    cleaned_sentence = (soup.recording.cleaned_sentence.string).strip()
                    sentence_id = int((soup.recording.sentence_id.string).strip())

                    speaker_id = (soup.recording.speaker_id.string).strip()
                    gender     = (soup.recording.gender.string).strip()
                    name       = 'gsp%s' % speaker_id.replace('-','')
                    speakerdir = '%s/%s' % (destdir, name)

                    if not speaker_id in speakers:

                        speakers.add(speaker_id)

                        genderf.write('%s %s\n' % (name, 'm' if gender=='male' else 'f'))

                        # print speakerdir
                        mkdirs('%s/wav' % speakerdir)
                        mkdirs('%s/etc' % speakerdir)

                    for mic in ['Yamaha', 'Kinect-Beam', 'Kinect-RAW', 'Realtek', 'Samson']:

                        srcaudiofn = '%s/%s_%s.wav' % (folder, fbase, mic)

                        if not os.path.isfile(srcaudiofn):
                            continue

                        audiofn = '%s-%s' % (fbase, mic)

                        dstaudiofn = '%s/wav/%s.wav' % (speakerdir, audiofn)

                        print '%5d/%5d %s %s %s' % (cnt_files, num_files, name, audiofn, srcaudiofn)

                        with open('%s/etc/prompts-original' % speakerdir, 'a') as promptsf:
                            promptsf.write((u'%s %s\n' % (audiofn, cleaned_sentence)).encode('utf8'))

                        copy_file(srcaudiofn, dstaudiofn)

