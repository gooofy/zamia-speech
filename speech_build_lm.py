#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Marc Puels
# Copyright 2013, 2014, 2016, 2017, 2019 Guenter Bartsch
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
# Train n-gram language model on tokenized text corpora
#
# The resulting language model will be written to the directory
# data/dst/lm/<language_model>/. The search path for the tokenized text
# corpora is data/dst/text-corpora.
#
# Example:
#
#     ./speech_build_lm.py my-language-model parole_de europarl_de
#
# A language model will be trained on the text corpora found in
# data/dst/text-corpora/parole_de.txt and
# data/dst/text-corpora/europarl_de.txt. The resulting language model
# will be written to the directory data/dst/lm/my-language-model/.
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

import codecs
import logging
import os
import sys

from optparse     import OptionParser

from nltools.misc import init_app, load_config, mkdirs

PROC_TITLE = 'speech_build_lm'

SENTENCES_STATS = 100000

LANGUAGE_MODELS_DIR = "data/dst/lm"
TEXT_CORPORA_DIR    = "data/dst/text-corpora"

def train_ngram_model(ngram_count_path, train_fn, lm_fn):
    cmd = '%s -text %s -order 3 -wbdiscount -interpolate -lm %s' % ( ngram_count_path, train_fn, lm_fn )

    logging.info(cmd)

    os.system(cmd)

def prune_ngram_model(ngram_path, lm_fn, lm_pruned_fn):
    # cmd = '%s -prune 1e-9 -lm %s -write-lm %s' % (ngram_path, lm_fn, lm_pruned_fn)
    cmd = '%s -prune 0.0000001 -lm %s -write-lm %s' % ( ngram_path, lm_fn, lm_pruned_fn )

    logging.info(cmd)

    os.system(cmd)

def train_pruned_model_with_kenlm(train_fn, lm_fn):
    cmd = 'lmplz --skip_symbols -o 4 -S 70%% --prune 0 3 5 --text %s > %s' % (train_fn, lm_fn)
    logging.info(cmd)
    os.system(cmd)

init_app(PROC_TITLE)

#
# config
#

config = load_config('.speechrc')

#
# commandline
#

parser = OptionParser("usage: %prog [options] <language_model> <text_corpus> [ <text_corpus2> ... ]")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0, help="debug limit")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="verbose output")

parser.add_option ("-k", "--kenlm", action="store_true", dest="kenlm", help="use KenLM instead of srilm")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) < 2:
    parser.print_usage()
    sys.exit(1)

if not options.kenlm:
    srilm_root = config.get("speech", "srilm_root")
    ngram_path = '%s/bin/i686-m64/ngram' % srilm_root
    ngram_count_path = '%s/bin/i686-m64/ngram-count' % srilm_root

    if not os.path.exists(ngram_path):
        logging.error("Could not find required executable %s" % ngram_path)
        sys.exit(1)

    if not os.path.exists(ngram_count_path):
        logging.error("Could not find required executable %s" % ngram_count_path)
        sys.exit(1)

language_model = args[0]
text_corpora   = args[1:]

outdir = '%s/%s' % (LANGUAGE_MODELS_DIR, language_model)
mkdirs(outdir)

train_fn = '%s/train_all.txt' % outdir 

num_sentences = 0

with codecs.open(str(train_fn), 'w', 'utf8') as dstf:
    for text_corpus_name in text_corpora:
        src = '%s/%s.txt' % (TEXT_CORPORA_DIR, text_corpus_name)
        logging.info('reading from sources %s' % src)
        with codecs.open(str(src), 'r', 'utf8') as srcf:
            while True:

                line = srcf.readline()
                if not line:
                    break

                dstf.write(line)

                num_sentences += 1
                if num_sentences % SENTENCES_STATS == 0:
                    logging.info('%8d sentences.' % num_sentences)

                if options.debug > 0 and num_sentences >= options.debug:
                    logging.warning(
                        'stopping because sentence debug limit is reached.')
                    break

logging.info('done. %s written, %d sentences.' % (train_fn, num_sentences))

lm_fn = '%s/lm_full.arpa' % outdir
lm_pruned_fn = '%s/lm.arpa' % outdir

if options.kenlm:
    train_pruned_model_with_kenlm(train_fn, lm_pruned_fn)
else:
    train_ngram_model(ngram_count_path, train_fn, lm_fn)
    prune_ngram_model(ngram_path, lm_fn, lm_pruned_fn)
