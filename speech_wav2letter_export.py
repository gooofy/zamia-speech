#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Copyright 2019 Guenter Bartsch
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
# export speech training data to create a wav2letter case
#

import sys
import logging
import os
import codecs

from optparse               import OptionParser

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa

from speech_lexicon         import Lexicon
from speech_transcripts     import Transcripts

APP_NAME            = 'speech_wav2letter_export'

LANGUAGE_MODELS_DIR = 'data/dst/lm'
ASR_MODELS_DIR      = 'data/dst/asr-models'


#
# main
#

misc.init_app(APP_NAME)

#
# commandline
#

parser = OptionParser("usage: %prog [options] <model_name> <dictionary> <language_model> <audio_corpus> [ <audio_corpus2> ... ]")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0, help="Limit number of sentences (debug purposes only), default: 0")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de', help="language (default: de)")

parser.add_option ("-p", "--prompt-words", action="store_true", dest="prompt_words", help="Limit dict to tokens covered in prompts")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) < 4:
    parser.print_usage()
    sys.exit(1)

model_name     = args[0]
dictionary     = args[1]
language_model = args[2]
audio_corpora  = args[3:]

language_model_dir = '%s/%s' % (LANGUAGE_MODELS_DIR, language_model)

if not os.path.isdir(language_model_dir):
    logging.error(
        "Could not find language model directory {}. Create a language "
        "model first with speech_build_lm.py.".format(language_model_dir))
    sys.exit(1)

work_dir = '%s/wav2letter/%s' % (ASR_MODELS_DIR, model_name)
data_dir = '%s/data' % work_dir

#
# config
#

config = misc.load_config ('.speechrc')

w2l_env_activate = config.get("speech", "w2l_env_activate")
w2l_train        = config.get("speech", "w2l_train")
wav16_dir        = config.get("speech", "wav16")

#
# create basic work dir structure
#

misc.mkdirs('%s/valid' % data_dir)
misc.mkdirs('%s/train' % data_dir)

#
# load dict
#

logging.info("loading lexicon...")
lex = Lexicon(file_name=dictionary)
logging.info("loading lexicon...done.")

#
# language model
#

misc.copy_file('%s/lm.arpa' % language_model_dir, '%s/lm.arpa' % data_dir)


#
# scripts
#

misc.render_template('data/src/speech/w2l_run_train.sh.template', '%s/run_train.sh' % work_dir, w2l_env_activate=w2l_env_activate, w2l_train=w2l_train)
misc.mkdirs('%s/config/conv_glu' % work_dir)
misc.render_template('data/src/speech/w2l_config_conv_glu_train.cfg.template', '%s/config/conv_glu/train.cfg' % work_dir, runname=model_name)
misc.copy_file('data/src/speech/w2l_config_conv_glu_network.arch', '%s/config/conv_glu/network.arch' % work_dir)

#
# export audio
#

def export_audio (train_val, tsdict):

    global data_dir, utt_num, options

    destdirfn = '%s/%s' % (data_dir, train_val)

    for utt_id in tsdict:

        with codecs.open('%s/%09d.id'  % (destdirfn, utt_num[train_val]), 'w', 'utf8') as idf,   \
             codecs.open('%s/%09d.tkn' % (destdirfn, utt_num[train_val]), 'w', 'utf8') as tknf,  \
             codecs.open('%s/%09d.wrd' % (destdirfn, utt_num[train_val]), 'w', 'utf8') as wrdf   :

            ts = tsdict[utt_id]

            tkn = u''
            wrd = u''
            for token in tokenize(ts['ts'], lang=options.lang):

                if not (token in lex):
                    logging.error(u'token %s missing from dict!' % token)
                    logging.error(u'utt_id: %s' % utt_id)
                    logging.error(u'ts: %s' % ts['ts'])
                    sys.exit(1)

                ipas = lex[token]['ipa'] 
                xsr = ipa2xsampa(token, ipas, spaces=True)

                xs = (xsr.replace('-', '')
                         .replace('\' ', '\'')
                         .replace('  ', ' ')
                         .replace('#', 'nC'))

                if tkn:
                    tkn += u' | '
                    wrd += u' '

                tkn += xs
                wrd += token
                
            tknf.write('%s\n' % tkn)
            wrdf.write('%s\n' % wrd)

            cmd = 'ln -s %s/%s/%s.wav %s/%09d.wav' % (wav16_dir, ts['corpus_name'], utt_id, destdirfn, utt_num[train_val])
            logging.debug(cmd)
            os.system(cmd)

            # utt2spkf.write('%s %s\n' % (utt_id, ts['spk']))

            utt_num[train_val] = utt_num[train_val] + 1

utt_num = { 'train': 0, 'valid': 0 }

for audio_corpus in audio_corpora:

    logging.info("exporting transcripts from %s ..." % audio_corpus)

    transcripts = Transcripts(corpus_name=audio_corpus)

    ts_all, ts_train, ts_test = transcripts.split(limit=options.debug)

    export_audio('train', ts_train)
    export_audio('valid', ts_test)

    logging.info("exported transcripts from %s: %d train, %d test samples." % (audio_corpus, len(ts_train), len(ts_test)))

#
# export dict
#

logging.info("Exporting dictionary...")

utt_dict = {}
for token in lex:
    utt_dict[token] = lex.dictionary[token]['ipa']

dictfn = '%s/lexicon.txt' % data_dir
phoneme_set = set()
with codecs.open(dictfn, 'w', 'utf8') as dictf:

    for token in sorted(utt_dict):

        ipa = utt_dict[token]
        xsr = ipa2xsampa(token, ipa, spaces=True)

        xs = (xsr.replace('-', '')
                 .replace('\' ', '\'')
                 .replace('  ', ' ')
                 .replace('#', 'nC'))

        dictf.write(u'%s %s\n' % (token, xs))

        for p in xs.split(' '):

            if len(p) < 1:
                logging.error(
                    u"****ERROR: empty phoneme in : '%s' ('%s', ipa: '%s', token: '%s')" % (
                    xs, xsr, ipa, token))

            phoneme_set.add(p)

logging.info("%s written." % dictfn)
logging.info("Exporting dictionary ... done.")

#
# export phoneme set
#

tokensfn = '%s/tokens.txt' % data_dir

with codecs.open(tokensfn, 'w', 'utf8') as tokensf:

    tokensf.write('|\n')

    for token in sorted(phoneme_set):
        tokensf.write(u'%s\n' % token)

logging.info("%s written." % tokensfn)

logging.info ( "All done." )

