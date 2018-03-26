#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import logging
import pickle

import nltk
import plac

import parole

from nltools.misc import init_app, load_config


@plac.annotations(
    verbose=("Enable verbose logging", "flag", "v"),
    debug_sgm_limit=("Limit number of sgm files for debugging purposes",
                     "option", None, int))
def main(verbose=False, debug_sgm_limit=0):
    """Train the Punkt tokenizer on the German Parole corpus"""
    init_app('speech_sentences')

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config('.speechrc')

    parole_path = config.get("speech", "parole_de")

    logging.info("training punkt...")

    punkt_trainer = nltk.tokenize.punkt.PunktTrainer()

    train_punkt_wrapper = parole.TrainPunktWrapper(punkt_trainer)

    parole.parole_crawl(parole_path, train_punkt_wrapper.train_punkt,
                        debug_sgm_limit)

    logging.info("finalizing punkt training...")
    punkt_trainer.finalize_training(verbose=True)
    logging.info("punkt training done. %d text segments."
                 % train_punkt_wrapper.punkt_count)

    params = punkt_trainer.get_params()
    # print "Params: %s" % repr(params)

    parole.PUNKT_PICKLEFN.parent.mkdir(parents=True, exist_ok=True)
    tokenizer = nltk.tokenize.punkt.PunktSentenceTokenizer(params)
    with open(str(parole.PUNKT_PICKLEFN), mode='wb') as f:
            pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)

    logging.info('%s written.' % parole.PUNKT_PICKLEFN)


if __name__ == "__main__":
    plac.call(main)
