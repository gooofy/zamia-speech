#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2017, 2018 Guenter Bartsch
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
# prepare tacotron datasets for zamia-tts
#


import sys
import re
import os
import ConfigParser
import codecs
import logging
import random
import json

import numpy as np

from optparse           import OptionParser
from nltools            import misc
from zamiatts           import DSFN_PATH, DSFN_X, DSFN_XL, DSFN_YS, DSFN_YM, DSFN_YL, VOICE_PATH, HPARAMS_SRC, DSFN_HPARAMS, cleanup_text
from zamiatts           import audio
from speech_transcripts import Transcripts

DEBUG_LIMIT  = 0
# DEBUG_LIMIT = 4096
# DEBUG_LIMIT = 512

PROC_TITLE      = 'ztts_prepare'
MIN_QUALITY     = 2

def _decode_input(x):

    global hparams

    res = u''

    for c in x:
        if c:
            res += hparams['alphabet'][c]

    return res

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# config
#

config = misc.load_config('.speechrc')

speech_corpora_dir = config.get("speech", "speech_corpora")
wav16_dir          = config.get("speech", "wav16")

#
# command line
#

speech_corpora_available = []
for corpus in os.listdir(speech_corpora_dir):
    if not os.path.isdir('%s/%s' % (speech_corpora_dir, corpus)):
        continue
    speech_corpora_available.append(corpus)

parser = OptionParser("usage: %%prog [options] <corpus> <speaker_in> <speaker_out>\n  corporus: one of %s" % ", ".join(speech_corpora_available))

parser.add_option ("-l", "--lang", dest="lang", type = "str", default="de",
                   help="language (default: de)")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")


(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 3:
    parser.print_help()
    sys.exit(0)

corpus_name  = args[0]
speaker_in   = args[1]
speaker_out  = args[2]
lang         = options.lang

#
# clean up / setup directories
#

cmd = 'rm -rf %s' % (DSFN_PATH % speaker_out)
logging.info(cmd)
os.system(cmd)

cmd = 'mkdir -p %s' % (DSFN_PATH % speaker_out)
logging.info(cmd)
os.system(cmd)

cmd = 'cp %s %s' % (HPARAMS_SRC % lang, DSFN_HPARAMS % speaker_out)
logging.info(cmd)
os.system(cmd)

#
# globals
#

with codecs.open(DSFN_HPARAMS % speaker_out, 'r', 'utf8') as hpf:
    hparams         = json.loads(hpf.read())
max_inp_len     = hparams['max_inp_len']
max_num_frames  = hparams['max_iters'] * hparams['outputs_per_step'] * hparams['frame_shift_ms'] * hparams['sample_rate'] / 1000

n_fft, hop_length, win_length = audio.stft_parameters(hparams)
max_mfc_frames  = 1 + int((max_num_frames - n_fft) / hop_length)

logging.info ('max_mfc_frames=%d, num_freq=%d, num_mels=%d' % (max_mfc_frames,hparams['num_freq'],hparams['num_mels']))

#
# main
#

logging.info ('reading transcripts from %s ...' % corpus_name)

transcripts = Transcripts(corpus_name=corpus_name)

cnt = 0
num_skipped = 0

input_data     = np.zeros( (1, max_inp_len), dtype='int32')
input_lengths  = np.zeros( (1, ), dtype='int32')
target_data_s  = np.zeros( (1, max_mfc_frames, hparams['num_freq']) , dtype='float32')
target_data_m  = np.zeros( (1, max_mfc_frames, hparams['num_mels']) , dtype='float32')
target_lengths = np.zeros( (1, ), dtype='int32')

for cfn in transcripts:

    ts = transcripts[cfn]

    if ts['quality'] < MIN_QUALITY:
        continue

    if ts['spk'] != speaker_in:
        continue

    ts_orig  = ts['ts']
    ts_clean = cleanup_text(ts_orig, lang, hparams['alphabet'])
    logging.debug(u'ts_orig : %s' % ts_orig)
    logging.debug(u'ts_clean: %s' % ts_clean)

    if len(ts_clean) > (max_inp_len-1):
        num_skipped += 1
        pskipped = num_skipped * 100 / (cnt + num_skipped)
        logging.error('%6d %-20s: transcript too long (%4d > %4d) %3d%% skipped' % (cnt, cfn, len(ts_clean), max_inp_len, pskipped))
        continue

    wavfn = '%s/%s/%s.wav' % (wav16_dir, corpus_name, cfn)
    wav = audio.load_wav(wavfn)

    if wav.shape[0] < 512:
        num_skipped += 1
        pskipped = num_skipped * 100 / (cnt + num_skipped)
        logging.error('%6d %-20s: audio too short (%4d < 512) %3d%% skipped' % (cnt, cfn, len(ts_clean), pskipped))
        continue

    spectrogram     = audio.spectrogram(wav, hparams).astype(np.float32)
    mel_spectrogram = audio.melspectrogram(wav, hparams).astype(np.float32)

    if spectrogram.shape[1] > (max_mfc_frames-1):
        num_skipped += 1
        pskipped = num_skipped * 100 / (cnt + num_skipped)
        logging.error('%6d %-20s: audio too long (%4d > %4d) %3d%% skipped' % (cnt, cfn, spectrogram.shape[1], max_mfc_frames, pskipped))
        continue

    logging.info('%6d %-20s: ok, spectrogram.shape=%s, mel_spectrogram.shape=%s' % (cnt, cfn, spectrogram.shape, mel_spectrogram.shape))

    # numpy conversion

    S = spectrogram.T
    M = mel_spectrogram.T

    input_data[0].fill(0)

    for j, c in enumerate(ts_clean):
        c_enc = hparams['alphabet'].find(c)
        if c_enc<0:
            logging.error('missing char in alphabet: %s' % c)
            # c_enc = hparams['alphabet'].find(u' ')

        input_data[0, j] = c_enc

    ts_dec = _decode_input(input_data[0])

    input_lengths[0] = len(ts_dec) + 1 # +1 for start symbol

    target_data_s[0]  = np.pad(S, ((0, max_mfc_frames - S.shape[0]), (0,0)), 'constant', constant_values=(0.0,0.0))
    target_data_m[0]  = np.pad(M, ((0, max_mfc_frames - S.shape[0]), (0,0)), 'constant', constant_values=(0.0,0.0))
    target_lengths[0] = S.shape[0] + 1

    np.save(DSFN_X % (speaker_out, cnt), input_data)
    logging.debug("%s written. %s" % (DSFN_X % (speaker_out, cnt), input_data.shape))

    np.save(DSFN_XL % (speaker_out, cnt), input_lengths)
    logging.debug("%s written. %s" % (DSFN_XL % (speaker_out, cnt), input_lengths.shape))

    np.save(DSFN_YS % (speaker_out, cnt), target_data_s)
    logging.debug("%s written. %s" % (DSFN_YS % (speaker_out, cnt), target_data_s.shape))

    np.save(DSFN_YM % (speaker_out, cnt), target_data_m)
    logging.debug("%s written. %s" % (DSFN_YM % (speaker_out, cnt), target_data_m.shape))

    np.save(DSFN_YL % (speaker_out, cnt), target_lengths)
    logging.debug("%s written. %s" % (DSFN_YL % (speaker_out, cnt), target_lengths.shape))

    cnt += 1
    if DEBUG_LIMIT and cnt >= DEBUG_LIMIT:
        logging.warn ('DEBUG LIMIT REACHED.')
        break

