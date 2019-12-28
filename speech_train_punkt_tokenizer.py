#!/usr/bin/env python2
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
# scan voxforge and kitchen dirs for new audio data and transcripts
# convert to 16kHz wav, add transcripts entries
#

import logging
import pickle
import os
import nltk

from optparse     import OptionParser

import parole

from nltools.misc import init_app, load_config, mkdirs

#
# init 
#

init_app ('speech_train_punkt_tokenizer')

config = load_config ('.speechrc')

parole_path = config.get("speech", "parole_de")

#
# command line
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-l", "--sgm-limit", dest="debug_sgm_limit", type="int", default=0,
                   help="Limit number of sgm files for debugging purposes (default: no limit)")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


#
# main
#

logging.info("training punkt...")

punkt_trainer = nltk.tokenize.punkt.PunktTrainer()

train_punkt_wrapper = parole.TrainPunktWrapper(punkt_trainer)

parole.parole_crawl(parole_path, train_punkt_wrapper.train_punkt,
                    options.debug_sgm_limit)

logging.info("finalizing punkt training...")
punkt_trainer.finalize_training(verbose=True)
logging.info("punkt training done. %d text segments."
             % train_punkt_wrapper.punkt_count)

params = punkt_trainer.get_params()
# print "Params: %s" % repr(params)

mkdirs(os.path.dirname(parole.PUNKT_PICKLEFN))

tokenizer = nltk.tokenize.punkt.PunktSentenceTokenizer(params)
with open(str(parole.PUNKT_PICKLEFN), mode='wb') as f:
        pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)

logging.info('%s written.' % parole.PUNKT_PICKLEFN)


