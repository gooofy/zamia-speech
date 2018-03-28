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

import codecs
import logging
import os
import sys

import plac
from pathlib2 import Path

from nltools.misc import init_app, load_config

TEXT_CORPORA_BASE_PATH = Path("data/dst/speech/text-corpora")
SENTENCES_STATS = 100000


@plac.annotations(
    language_model="The name of the resulting language model.",
    debug=("limit number of sentences (debug purposes only), default: 0 "
           "(unlimited)", "option", "d", int),
    verbose=("Enable verbose logging", "flag", "v"),
    text_corpus="Names of the text corpora to be used to train a language "
                "model.")
def main(language_model, debug=0, verbose=False, *text_corpus):
    """Train n-gram language model on tokenized text corpora

    The resulting language model will be written to the directory
    data/dst/speech/lm/<language_model>/. The search path for the tokenized text
    corpora is data/dst/speech/text-corpora.

    Example:

        ./speech_build_lm.py my-language-model parole_de europarl_de

    A language model will be trained on the text corpora found in
    data/dst/speech/text-corpora/parole_de.txt and
    data/dst/speech/text-corpora/europarl_de.txt. The resulting language model
    will be written to the directory data/dst/speech/my-language-model/.
    """
    init_app('speech_build_lm')

    if len(text_corpus) < 1:
        logging.error("Argument text_corpus missing, at least one is "
                      "required.")
        sys.exit(1)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config('.speechrc')
    srilm_root = config.get("speech", "srilm_root")
    ngram_path = Path('%s/bin/i686-m64/ngram' % srilm_root)
    ngram_count_path = Path('%s/bin/i686-m64/ngram-count' % srilm_root)

    if not ngram_path.exists():
        logging.error("Could not find required executable %s" % ngram_path)
        sys.exit(1)

    if not ngram_count_path.exists():
        logging.error("Could not find required executable %s" %
                      ngram_count_path)
        sys.exit(1)

    outdir = Path('data/dst/speech/lm/%s' % language_model)
    outdir.mkdir(parents=True, exist_ok=True)

    train_fn = outdir / "train_all.txt"

    num_sentences = 0

    with codecs.open(str(train_fn), 'w', 'utf8') as dstf:
        for text_corpus_name in text_corpus:
            src = TEXT_CORPORA_BASE_PATH / (text_corpus_name + ".txt")
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

                    if debug > 0 and num_sentences >= debug:
                        logging.warning(
                            'stopping because sentence debug limit is reached.')
                        break

    logging.info('done. %s written, %d sentences.' % (train_fn, num_sentences))

    lm_fn = outdir / 'lm_full.arpa'
    train_ngram_model(ngram_count_path, train_fn, lm_fn)

    lm_pruned_fn = outdir / 'lm.arpa'
    prune_ngram_model(ngram_path, lm_fn, lm_pruned_fn)


def train_ngram_model(ngram_count_path, train_fn, lm_fn):
    cmd = '%s -text %s -order 3 -wbdiscount -interpolate -lm %s' % (
        ngram_count_path, train_fn, lm_fn)

    logging.info(cmd)

    os.system(cmd)


def prune_ngram_model(ngram_path, lm_fn, lm_pruned_fn):
    # cmd = '%s -prune 1e-9 -lm %s -write-lm %s' % (ngram_path, lm_fn, lm_pruned_fn)
    cmd = '%s -prune 0.0000001 -lm %s -write-lm %s' % (
        ngram_path, lm_fn, lm_pruned_fn)

    logging.info(cmd)

    os.system(cmd)


if __name__ == "__main__":
    plac.call(main)
