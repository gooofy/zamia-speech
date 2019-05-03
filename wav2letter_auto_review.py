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
# export corpus entries that are not reviewed yet for w2l auto-review
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

APP_NAME            = 'wav2letter_auto_review'

WORK_DIR            = 'tmp/w2letter_auto_review'

CUDA_DEVICE         = '1'
WAV_MIN_SIZE        = 1024

#
# main
#

misc.init_app(APP_NAME)

#
# commandline
#

parser = OptionParser("usage: %prog [options] <model> <audio_corpus>")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0, help="Limit number of sentences (debug purposes only), default: 0")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de', help="language (default: de)")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", help="verbose output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 2:
    parser.print_usage()
    sys.exit(1)

model_name     = args[0]
audio_corpus   = args[1]

data_dir = '%s/data' % WORK_DIR

#
# config
#

config = misc.load_config ('.speechrc')

w2l_env_activate = config.get("speech", "w2l_env_activate")
w2l_decoder      = config.get("speech", "w2l_decoder")
wav16_dir        = config.get("speech", "wav16")

#
# create basic work dir structure
#

cmd = 'rm -rf %s' % WORK_DIR
logging.debug(cmd)
os.system(cmd)
misc.mkdirs('%s/test' % data_dir)

#
# scripts
#
 
misc.render_template('data/src/speech/w2l_run_auto_review.sh.template', '%s/run_auto_review.sh' % WORK_DIR, 
                     w2l_env_activate = w2l_env_activate, 
                     w2l_decoder      = w2l_decoder,
                     cuda_device      = CUDA_DEVICE,
                     w2l_tokensdir    = '../../data/models/%s' % model_name,
                     w2l_tokens       = 'tokens.txt',
                     w2l_lexicon      = '../../data/models/%s/lexicon.txt' % model_name,
                     w2l_am           = '../../data/models/%s/model.bin' % model_name,
                     w2l_lm           = 'data/lm6.bin')
#
# read lexicon
#

lexfn = 'data/models/%s/lexicon.txt' % model_name

logging.info('reading lexicon %s ...' % lexfn)

lex = {}

with codecs.open(lexfn, 'r', 'utf8') as lexf:
    for line in lexf:
        parts = line.strip().split(' ')
        lex[parts[0]] = ' '.join(parts[1:])

logging.info('reading lexicon %s ... done. %d entries.' % (lexfn, len(lex)))
# print repr(lex)

#
# export audio, prompts (for lm)
#

logging.info("exporting transcripts from %s ..." % audio_corpus)

transcripts = Transcripts(corpus_name=audio_corpus)

utt_num = 0

destdirfn = '%s/test' % data_dir

prompts = set()

for utt_id in transcripts:

    ts = transcripts[utt_id]
    prompts.add(u' '.join(tokenize(transcripts[utt_id]["prompt"], options.lang)))

    if ts['quality'] != 0:
        continue

    wavfn = '%s/%s/%s.wav' % (wav16_dir, ts['corpus_name'], utt_id)
    if not os.path.exists(wavfn):
        logging.error('%s missing!' % wavfn)
        continue

    if os.path.getsize(wavfn) < WAV_MIN_SIZE:
        logging.error('%s is too short!' % wavfn)
        continue
        

    with codecs.open('%s/%09d.id'  % (destdirfn, utt_num), 'w', 'utf8') as idf,   \
         codecs.open('%s/%09d.tkn' % (destdirfn, utt_num), 'w', 'utf8') as tknf,  \
         codecs.open('%s/%09d.wrd' % (destdirfn, utt_num), 'w', 'utf8') as wrdf   :

        tkn = u''
        wrd = u''
        for token in tokenize(ts['prompt'], lang=options.lang):

            if not (token in lex):
                logging.error(u'token %s missing from dict!' % token)
                logging.error(u'utt_id: %s' % utt_id)
                logging.error(u'ts: %s' % ts['ts'])
                sys.exit(1)

            xs = lex[token]

            if tkn:
                tkn += u' | '
                wrd += u' '

            tkn += xs
            wrd += token
            
        tknf.write('%s\n' % tkn)
        wrdf.write('%s\n' % wrd)
        idf.write('utt_id\t%s\ncorpus\t%s\nlang\t%s\n' % (utt_id, audio_corpus, options.lang))

        cmd = 'ln -s %s %s/%09d.wav' % (wavfn, destdirfn, utt_num)
        logging.debug(cmd)
        os.system(cmd)

        utt_num = utt_num + 1

        if options.debug>0 and utt_num >= options.debug:
            logging.warn('debug limit reached!')
            break

        if utt_num % 100 == 0:
            logging.info ("%5d transcripts..." % utt_num)

logging.info("exporting transcripts from %s ... done. %d utts." % (audio_corpus, utt_num))

#
# language model
#

logging.info('creating language model...')

promptsfn = '%s/prompts.txt' % data_dir
with codecs.open(promptsfn, 'w', 'utf8') as promptsf:
    for p in prompts:
        promptsf.write(u'%s\n' % p)

cmd = 'lmplz --skip_symbols -o 6 -S 70%% --prune 0 0 0 0 1 --text %s > %s/lm6.arpa' % (promptsfn, data_dir)
logging.debug(cmd)
os.system(cmd)

cmd = 'kenlm_build_binary %s/lm6.arpa %s/lm6.bin' % (data_dir, data_dir)
logging.debug(cmd)
os.system(cmd)

logging.info('language model %s/lm6.bin is done.' % data_dir)

#
# finish
#

logging.info('all done. next steps: cd tmp/w2letter_auto_review ; bash run_auto_review.sh')

