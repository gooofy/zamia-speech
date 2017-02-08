#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017 Guenter Bartsch
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
# train LM using srilm
#

# lmdir=data/local/lm
# lang=data/lang_test
# 
# if [ -f path.sh ]; then
#       . path.sh; else
#          echo "missing path.sh"; exit 1;
# fi
# 
# export LC_ALL=C
# . ./path.sh || exit 1; # for KALDI_ROOT
# export PATH=$KALDI_ROOT/tools/srilm/bin:$KALDI_ROOT/tools/srilm/bin/i686-m64:$PATH
# export LD_LIBRARY_PATH="$KALDI_ROOT/tools/liblbfgs-1.10/lib/.libs:$LD_LIBRARY_PATH"
# 
# rm -rf data/lang_test
# cp -r data/lang data/lang_test
# 
# echo
# echo "create train_all.txt"
# 
# cat $lmdir/train_nounk.txt ../sentences.txt > $lmdir/train_all.txt
# 
# echo
# echo "ngram-count..."
# 
# ngram-count -text $lmdir/train_all.txt -order 3 \
#                 -wbdiscount -interpolate -lm $lmdir/lm.arpa
#

import sys
import os
import traceback
import codecs
import logging

from optparse import OptionParser

from nltools.misc import load_config, init_app, mkdirs
from nltools.tokenizer import tokenize
from speech_transcripts import Transcripts

WORKDIR = 'data/dst/speech/%s/srilm'

SOURCES = ['data/dst/speech/%s/sentences.txt',
           'data/dst/speech/%s/nlp-sentences.txt']

SENTENCES_STATS      = 100000

#
# init 
#

init_app ('speech_build_lm')

config = load_config ('.speechrc')

kaldi_root       = config.get("speech", "kaldi_root")
ngram_path       = '%s/tools/srilm/bin/i686-m64/ngram' % kaldi_root
ngram_count_path = '%s/tools/srilm/bin/i686-m64/ngram-count' % kaldi_root

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0,
                   help="limit number of sentences (debug purposes only), default: 0 (unlimited)")
parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")
parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

work_dir = WORKDIR % options.lang

logging.info ('work_dir: %s' % work_dir)

logging.info ("loading transcripts...")
transcripts = Transcripts()
logging.info ("loading transcripts... done.")

#
# merge sentences
#

logging.info ('merging sentence sources...')

mkdirs('%s' % work_dir)

num_sentences = 0

train_fn = '%s/train_all.txt' % work_dir

with codecs.open (train_fn, 'w', 'utf8') as dstf:

    logging.info ('adding transcripts...')
    for cfn in transcripts:
        ts = transcripts[cfn]['ts']
        if len(ts)<2:
            continue

        dstf.write(u'%s\n' % ts)

        num_sentences += 1
        if num_sentences % SENTENCES_STATS == 0:
            logging.info ('%8d sentences.' % num_sentences)

    for src in SOURCES:

        logging.info ('reading from sources %s' % src)

        with codecs.open (src % options.lang, 'r', 'utf8') as srcf:

            while True:
                
                line = srcf.readline()
                if not line:
                    break

                dstf.write(line)

                num_sentences += 1
                if num_sentences % SENTENCES_STATS == 0:
                    logging.info ('%8d sentences.' % num_sentences)

                if options.debug>0 and num_sentences >= options.debug:
                    logging.warning ('stopping because sentence debug limit is reached.')
                    break

logging.info ('done. %s written, %d sentences.' % (train_fn, num_sentences))

#
# ngram-count
#

lm_fn = '%s/lm.arpa' % work_dir

cmd = '%s -text %s -order 3 -wbdiscount -interpolate -lm %s' % (ngram_count_path, train_fn, lm_fn)

logging.info (cmd)

os.system(cmd)

#
# prune
#

lm_pruned_fn = '%s/lm.arpa' % work_dir

cmd = '%s -prune 1e-9 -lm %s -write-lm %s' % (ngram_path, lm_fn, lm_pruned_fn)

logging.info (cmd)

os.system(cmd)

