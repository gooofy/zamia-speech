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
