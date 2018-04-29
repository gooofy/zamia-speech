#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Copyright 2018 Marc Puels
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
# scan voxforge and kitchen dirs for new audio data and transcripts
# convert to 16kHz wav, add transcripts entries
#

import codecs
import json
import logging
import os

import plac

from nltools.misc import init_app, load_config
from nltools.tokenizer import tokenize

import parole

from parole import load_punkt_tokenizer
from paths import TEXT_CORPORA_DIR
from speech_transcripts import Transcripts


TEXT_CORPORA = {
    "cornell_movie_dialogs":
        lambda corpus_path: proc_cornell_movie_dialogs(corpus_path, tokenize),
    "europarl_de":
        lambda corpus_path: proc_europarl_de(corpus_path, tokenize),
    "europarl_en":
        lambda corpus_path: proc_europarl_en(corpus_path, tokenize),
    "parole_de":
        None,
    "web_questions":
        lambda corpus_path: proc_web_questions(corpus_path, tokenize),
    "yahoo_answers":
        lambda corpus_path: proc_yahoo_answers(corpus_path, tokenize),
}

SPEECH_CORPORA = {
    "forschergeist":
        lambda: proc_transcripts("forschergeist"),
    "gspv2":
        lambda: proc_transcripts("gspv2"),
    "voxforge_de":
        lambda: proc_transcripts("voxforge_de"),
    "zamia_de":
        lambda: proc_transcripts("zamia_de"),
}

CORPORA = {}
CORPORA.update(TEXT_CORPORA)
CORPORA.update(SPEECH_CORPORA)

SENTENCES_STATS = 1000
DEBUG_LIMIT = 0
DEBUG_SGM_LIMIT_PAROLE = 0


@plac.annotations(
    corpus=("Name of corpus to extract sentences from.",
            "positional", None, str, sorted(CORPORA.keys())),
    verbose=("Enable verbose logging", "flag", "v"))
def main(corpus, verbose=False):
    """Generate training sentences for language models

    Let text_corpus be the argument given on the command line.
    Then the corpus text_corpus is tokenized and each sentence is written on a
    separate line into `data/dst/text-corpora/<text_corpus>.txt`. All
    punctuation marks are stripped.
    """
    init_app('speech_sentences')

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config('.speechrc')

    TEXT_CORPORA_DIR.mkdir(parents=True, exist_ok=True)

    out_file = TEXT_CORPORA_DIR / (corpus + ".txt")

    with codecs.open(str(out_file), "w", "utf-8") as outf:
        # I haven't figured out how to refactor the processing algorithms of the
        # parole corpus to implement a generator.
        if corpus == "parole_de":
            corpus_path = config.get("speech", corpus)
            proc_parole_de(corpus_path, load_punkt_tokenizer, outf)
        elif corpus in TEXT_CORPORA:
            corpus_path = config.get("speech", corpus)
            for sentence in TEXT_CORPORA[corpus](corpus_path):
                outf.write(sentence + "\n")
        elif corpus in SPEECH_CORPORA:
            for sentence in SPEECH_CORPORA[corpus]():
                outf.write(sentence + "\n")
        else:
            raise Exception("This shouldn't happen.")

    logging.info('%s written.' % out_file)


def proc_cornell_movie_dialogs(corpus_path, tokenize):
    num_sentences = 0
    with codecs.open('%s/movie_lines.txt' % corpus_path, 'r',
                     'latin1') as inf:
        for line in inf:
            parts = line.split('+++$+++')
            if not len(parts) == 5:
                logging.warn('movie dialogs: skipping line %s' % line)
                continue

            sentence = u' '.join(tokenize(parts[4], lang='en'))

            if not sentence:
                logging.warn('movie dialogs: skipping null sentence %s' % line)
                continue

            yield u'%s' % sentence

            num_sentences += 1
            if num_sentences % SENTENCES_STATS == 0:
                logging.info('movie dialogs: %8d sentences.' % num_sentences)

            if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                logging.warn('movie dialogs: debug limit reached, stopping.')
                break


def proc_europarl_de(corpus_path, tokenize):
    logging.info("adding sentences from europarl...")
    num_sentences = 0
    with codecs.open(corpus_path, 'r', 'utf8') as inf:
        for line in inf:
            yield u'%s' % ' '.join(tokenize(line))

            num_sentences += 1
            if num_sentences % SENTENCES_STATS == 0:
                logging.info ('%8d sentences.' % num_sentences)


def proc_europarl_en(corpus_path, tokenize):
    logging.info("adding sentences from europarl...")
    num_sentences = 0
    with codecs.open(corpus_path, 'r', 'utf8') as inf:
        for line in inf:

            sentence = u' '.join(tokenize(line, lang='en'))

            if not sentence:
                logging.warn('europarl: skipping null sentence.')
                continue

            yield u'%s' % sentence

            num_sentences += 1
            if num_sentences % SENTENCES_STATS == 0:
                logging.info('europarl: %8d sentences.' % num_sentences)

            if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                logging.warn('europarl: debug limit reached, stopping.')
                break


def proc_parole_de(corpus_path, load_punkt_tokenizer, outf):
    punkt_tokenizer = load_punkt_tokenizer()

    apply_punkt_wrapper = parole.ApplyPunktWrapper(punkt_tokenizer, outf)

    parole.parole_crawl(corpus_path, apply_punkt_wrapper.apply_punkt,
                        DEBUG_SGM_LIMIT_PAROLE)


def proc_web_questions(corpus_path, tokenize):
    num_sentences = 0
    for infn in ['webquestions.examples.test.json',
                 'webquestions.examples.train.json']:
        with open('%s/%s' % (corpus_path, infn), 'r') as inf:

            data = json.loads(inf.read())

            for a in data:

                sentence = u' '.join(tokenize(a['utterance'], lang='en'))

                if not sentence:
                    logging.warn(
                        'web questions: skipping null sentence')
                    continue

                yield u'%s' % sentence

                num_sentences += 1
                if num_sentences % SENTENCES_STATS == 0:
                    logging.info(
                        'web questions: %8d sentences.' % num_sentences)

                if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                    logging.warn(
                        'web questions: debug limit reached, stopping.')
                    break


def proc_yahoo_answers(corpus_path, tokenize):
    num_sentences = 0
    for infn in os.listdir('%s/text' % corpus_path):

        logging.debug('yahoo answers: reading file %s' % infn)

        with codecs.open('%s/text/%s' % (corpus_path, infn), 'r',
                         'latin1') as inf:
            for line in inf:
                sentence = u' '.join(tokenize(line, lang='en'))

                if not sentence:
                    continue

                yield u'%s' % sentence

                num_sentences += 1
                if num_sentences % SENTENCES_STATS == 0:
                    logging.info(
                        'yahoo answers: %8d sentences.' % num_sentences)

                if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                    logging.warn(
                        'yahoo answers: debug limit reached, stopping.')
                    break

        if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
            logging.warn('yahoo answers: debug limit reached, stopping.')
            break


def proc_transcripts(corpus_name):
    transcripts = Transcripts(corpus_name=corpus_name)
    transcripts_set = set((transcripts[key]["ts"] for key in transcripts))
    for ts in transcripts_set:
        yield ts


if __name__ == "__main__":
    plac.call(main)
