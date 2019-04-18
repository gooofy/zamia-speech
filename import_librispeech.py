#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2017, 2018 Guenter Bartsch
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
# convert(symlink) librivox corpus to a voxforge-like directory structure
# so we can import it using our regular tools
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

PROC_TITLE='librispeech_to_vf'

SUBSETS = set(['dev-clean', 'test-clean', 'train-clean-100', 'train-clean-360'])

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
# config
#

config = misc.load_config('.speechrc')

speech_arc     = config.get("speech", "speech_arc")
speech_corpora = config.get("speech", "speech_corpora")

srcdir  = '%s/LibriSpeech' % speech_arc
destdir = '%s/librispeech' % speech_corpora

misc.mkdirs(destdir)

#
# speakers
#

with open ('spk2gender.txt', 'w') as genderf:
    with open ('%s/SPEAKERS.TXT' % srcdir, 'r') as speakersf:

        for line in speakersf:
            if not line or line[0]==';':
                continue
            parts = line.split('|')

            if len(parts) < 5:
                logging.warn('speakers: skipping line %s' % line)

            speaker_id = 'librispeech'+parts[0].strip()
            sex        = parts[1].strip().lower()
            subset     = parts[2].strip()

            if not subset in SUBSETS:
                continue

            genderf.write('%s %s\n' % (speaker_id, sex))
        
#
# audio, prompts
#

for subset in os.listdir(srcdir):

    if not subset in SUBSETS:
        continue

    for speaker in os.listdir(srcdir + '/' + subset):
        for book_id in os.listdir(srcdir + '/' + subset + '/' + speaker):
            
            folder = 'librispeech%s-%s' % (speaker, book_id)
            dstdir = '%s/%s' % (destdir, folder)

            misc.mkdirs('%s/flac' % dstdir)
            misc.mkdirs('%s/etc' % dstdir)

            promptsfn = '%s/etc/prompts-original' % dstdir
            transfn = '%s/%s/%s/%s/%s-%s.trans.txt' % (srcdir, subset, speaker, book_id, speaker, book_id)

            with codecs.open (promptsfn, 'w', 'utf8') as promptsf:
                with codecs.open(transfn, 'r', 'utf8') as transf:
                    for line in transf:
                        parts = line.split()
                        promptsf.write(line)

                        flac_src = '%s/%s/%s/%s/%s.flac' % (srcdir, subset, speaker, book_id, parts[0])
                        flac_dst = '%s/flac/%s.flac' % (dstdir, parts[0])

                        logging.debug (' %s -> %s' % (flac_src, flac_dst))

                        misc.symlink(flac_src, flac_dst)


            logging.debug ('%s written.' % promptsfn)

