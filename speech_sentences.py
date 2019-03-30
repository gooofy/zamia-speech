#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Copyright 2018 Marc Puels
# Copyright 2013, 2014, 2016, 2017, 2018, 2019 Guenter Bartsch
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
# Generate training sentences for language models
#
# Let text_corpus be the argument given on the command line.
# Then the corpus text_corpus is tokenized and each sentence is written on a
# separate line into `data/dst/text-corpora/<text_corpus>.txt`. All
# punctuation marks are stripped.
#

import codecs
import json
import logging
import os
import sys

from optparse           import OptionParser
from nltools            import misc
from nltools.tokenizer  import tokenize

import parole

from parole             import load_punkt_tokenizer
from speech_transcripts import Transcripts

PROC_TITLE             = 'speech_sentences'

SENTENCES_STATS        = 1000

DEBUG_LIMIT            = 0
DEBUG_SGM_LIMIT_PAROLE = 0

TEXT_CORPORA_DIR = 'data/dst/text-corpora'

TEXT_CORPORA = {
    "cornell_movie_dialogs":
        lambda corpus_path: proc_cornell_movie_dialogs(corpus_path, tokenize),
    "europarl_de":
        lambda corpus_path: proc_europarl_de(corpus_path, tokenize),
    "europarl_en":
        lambda corpus_path: proc_corpus_with_one_sentence_perline(corpus_path, tokenize, 'en'),
    "europarl_fr":
        lambda corpus_path: proc_corpus_with_one_sentence_perline(corpus_path, tokenize, 'fr'),
    "est_republicain":
        lambda corpus_path: proc_corpus_with_one_sentence_perline(corpus_path, tokenize, 'fr'),
    "parole_de":
        None,
    "web_questions":
        lambda corpus_path: proc_web_questions(corpus_path, tokenize),
    "yahoo_answers":
        lambda corpus_path: proc_yahoo_answers(corpus_path, tokenize),
}

SPEECH_CORPORA = {
    "cv_corpus_v1":
        lambda: proc_transcripts("cv_corpus_v1"),
    "cv_de":
        lambda: proc_transcripts("cv_de"),
    "cv_fr":
        lambda: proc_transcripts("cv_fr"),
    "forschergeist":
        lambda: proc_transcripts("forschergeist"),
    "gspv2":
        lambda: proc_transcripts("gspv2"),
    "librispeech":
        lambda: proc_transcripts("librispeech"),
    "ljspeech":
        lambda: proc_transcripts("ljspeech"),
    "m_ailabs_de":
        lambda: proc_transcripts("m_ailabs_de"),
    "m_ailabs_en":
        lambda: proc_transcripts("m_ailabs_en"),
    "m_ailabs_fr":
        lambda: proc_transcripts("m_ailabs_fr"),
    "voxforge_de":
        lambda: proc_transcripts("voxforge_de"),
    "voxforge_en":
        lambda: proc_transcripts("voxforge_en"),
    "voxforge_fr":
        lambda: proc_transcripts("voxforge_fr"),
    "zamia_de":
        lambda: proc_transcripts("zamia_de"),
    "zamia_en":
        lambda: proc_transcripts("zamia_en"),
}

CORPORA = {}
CORPORA.update(TEXT_CORPORA)
CORPORA.update(SPEECH_CORPORA)

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


def proc_corpus_with_one_sentence_perline(corpus_path, tokenize, lang):
    logging.info("adding sentences from %s..." % corpus_path)
    num_sentences = 0
    with codecs.open(corpus_path, 'r', 'utf8') as inf:
        for line in inf:
            sentence = u' '.join(tokenize(line, lang=lang))

            if not sentence:
                logging.warn('%s: skipping null sentence.' % corpus_path)
                continue

            yield u'%s' % sentence

            num_sentences += 1
            if num_sentences % SENTENCES_STATS == 0:
                logging.info('%s: %8d sentences.' % (corpus_path, num_sentences))

            if DEBUG_LIMIT and num_sentences >= DEBUG_LIMIT:
                logging.warn('%s: debug limit reached, stopping.' % corpus_path)
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

    global use_prompts, lang

    transcripts = Transcripts(corpus_name=corpus_name)

    if use_prompts:
        transcripts_set = set((u' '.join(tokenize(transcripts[key]["prompt"], lang))) for key in transcripts)
    else:
        transcripts_set = set( (u' '.join(tokenize(transcripts[key]["ts"], lang)))  for key in transcripts )

    for ts in transcripts_set:
        yield ts


if __name__ == "__main__":

    misc.init_app(PROC_TITLE)

    #
    # config
    #

    config = misc.load_config('.speechrc')

    #
    # commandline
    #

    parser = OptionParser("usage: %%prog [options] <corpus>")

    parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                       help="language (default: de)")
    parser.add_option ("-p", "--prompts", action="store_true", dest="use_prompts",
                       help="extract original prompts instead of transcripts")
    parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                       help="verbose output")

    (options, args) = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    lang        = options.lang
    use_prompts = options.use_prompts

    if len(args) != 1:
        logging.error("Exactly one corpus (text or speech) must be provided.")

        parser.print_help()

        sys.exit(1)

    corpus = args[0]

    misc.mkdirs(TEXT_CORPORA_DIR)

    out_file = '%s/%s.txt' % (TEXT_CORPORA_DIR, corpus)

    with codecs.open(out_file, "w", "utf-8") as outf:
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


