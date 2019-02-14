#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Guenter Bartsch
# Copyright 2018 Keith Ito
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
#  tacotron model training frontend
#

import os
import re
import sys
import logging
import codecs

import numpy as np

from optparse             import OptionParser

from nltools              import misc
from zamiatts.tacotron    import Tacotron
from zamiatts             import audio, CHECKPOINT_DIR, EVAL_DIR, VOICE_PATH, DSFN_HPARAMS, HPARAMS_FN

PROC_TITLE      = 'ztts_train'

DEFAULT_NUM_EPOCHS = 10000

#
# init
#

misc.init_app(PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options] voice")

parser.add_option ("-n", "--num-epochs", dest="num_epochs", type="int", default=DEFAULT_NUM_EPOCHS,
                   help="number of epochs to train, default: %d" % DEFAULT_NUM_EPOCHS)

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

voice = args[0]

#
# clean up / setup directory
#

cmd = 'rm -rf %s' % (VOICE_PATH % voice)
logging.info(cmd)
os.system(cmd)

cmd = 'mkdir -p %s' % (VOICE_PATH % voice)
logging.info(cmd)
os.system(cmd)

cmd = 'cp %s %s' % (DSFN_HPARAMS % voice, HPARAMS_FN % voice)
logging.info(cmd)
os.system(cmd)

cmd = 'mkdir -p %s' % (CHECKPOINT_DIR % voice)
logging.info(cmd)
os.system(cmd)

cmd = 'mkdir -p %s' % (EVAL_DIR % voice)
logging.info(cmd)
os.system(cmd)


#
# training
#

taco = Tacotron(voice, is_training=True)

taco.train(num_epochs = options.num_epochs)

