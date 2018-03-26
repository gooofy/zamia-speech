#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import codecs
import json
import logging
import os

import plac

from pathlib2 import Path

from nltools.misc import init_app, load_config
from nltools.tokenizer import tokenize

import parole

from parole import load_punkt_tokenizer


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

SENTENCES_STATS = 1000
DEBUG_LIMIT = 0
DEBUG_SGM_LIMIT_PAROLE = 0


@plac.annotations(
    text_corpus=("Name of text corpus to extract sentences from.",
                 "positional", None, str, sorted(TEXT_CORPORA.keys())),
    verbose=("Enable verbose logging", "flag", "v"))
def main(text_corpus, verbose=False):
    """Generate training sentences for language models

    Let text_corpus be the argument given on the command line.
    Then the corpus text_corpus is tokenized and each sentence is written on a
    separate line into `data/dst/speech/text-corpora/<text_corpus>.txt`. All
    punctuation marks are stripped.
    """
    init_app('speech_sentences')

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config('.speechrc')

    corpus_path = config.get("speech", text_corpus)

    out_text_corpora_dir = Path("data/dst/speech/text-corpora")
    out_text_corpora_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_text_corpora_dir / (text_corpus + ".txt")

    with codecs.open(str(out_file), "w", "utf-8") as outf:
        # I haven't figured out how to refactor the processing algorithms of the
        # parole corpus to implement a generator.
        if text_corpus == "parole_de":
            proc_parole_de(corpus_path, load_punkt_tokenizer, outf)
        else:
            for sentence in TEXT_CORPORA[text_corpus](corpus_path):
                outf.write(sentence + "\n")

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

        with codecs.open('%s/text/%s' % (proc_yahoo_answers, infn), 'r',
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


if __name__ == "__main__":
    plac.call(main)
