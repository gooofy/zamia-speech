#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Copyright 2018 Marc Puels
# Copyright 2016, 2017, 2018, 2019 Guenter Bartsch
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
# export speech training data to create a kaldi case
#

import sys
import logging
import os

from optparse               import OptionParser

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa
from nltools.sequiturclient import sequitur_gen_ipa

from speech_lexicon         import Lexicon
from speech_transcripts     import Transcripts

SEQUITUR_MODEL_DIR  = 'data/models/sequitur'
LANGUAGE_MODELS_DIR = 'data/dst/lm'
ASR_MODELS_DIR      = 'data/dst/asr-models'

def export_kaldi_data (wav16_dir, audio_corpora, destdirfn, tsdict):
    logging.info ( "Exporting kaldi data to %s..." % destdirfn)

    misc.mkdirs(destdirfn)

    with open(destdirfn+'wav.scp','w') as wavscpf,  \
         open(destdirfn+'utt2spk','w') as utt2spkf, \
         open(destdirfn+'text','w') as textf:

        for utt_id in sorted(tsdict):
            ts = tsdict[utt_id]

            textf.write((u'%s %s\n' % (utt_id, ts['ts'])).encode('utf8'))

            wavscpf.write('%s %s/%s/%s.wav\n' % (utt_id, wav16_dir,
                                                 ts['corpus_name'], utt_id))

            utt2spkf.write('%s %s\n' % (utt_id, ts['spk']))

def add_missing_words(transcripts, lex, sequitur_model_path):
    logging.info("looking for missing words...")
    missing = {}  # word -> count
    num = len(transcripts)
    cnt = 0
    for cfn in transcripts:
        ts = transcripts[cfn]

        cnt += 1

        if ts['quality'] > 0:
            continue

        for word in tokenize(ts['prompt'], lang=options.lang):
            if word in lex:
                continue

            if word in missing:
                missing[word] += 1
            else:
                missing[word] = 1
    cnt = 0
    for item in reversed(sorted(missing.items(), key=lambda x: x[1])):
        lex_base = item[0]

        ipas = sequitur_gen_ipa(sequitur_model_path, lex_base)

        logging.info(u"%5d/%5d Adding missing word : %s [ %s ]" % (
        cnt, len(missing), item[0], ipas))

        lex_entry = {'ipa': ipas}
        lex[lex_base] = lex_entry
        cnt += 1

    return lex


def export_dictionary(ts_all, lex, dictfn2, prompt_words):
    logging.info("Exporting dictionary...")
    utt_dict = {}
    if prompt_words:
        for ts in ts_all:

            tsd = ts_all[ts]

            tokens = tsd['ts'].split(' ')

            # logging.info ( '%s %s' % (repr(ts), repr(tokens)) )

            for token in tokens:
                if token in utt_dict:
                    continue

                if not token in lex.dictionary:
                    logging.error(
                        "*** ERROR: missing token in dictionary: '%s' (tsd=%s, tokens=%s)" % (
                        token, repr(tsd), repr(tokens)))
                    sys.exit(1)

                utt_dict[token] = lex.dictionary[token]['ipa']
    else:
        for token in lex:
            utt_dict[token] = lex.dictionary[token]['ipa']

    ps = {}
    with open(dictfn2, 'w') as dictf:

        dictf.write('!SIL SIL\n')

        for token in sorted(utt_dict):

            ipa = utt_dict[token]
            xsr = ipa2xsampa(token, ipa, spaces=True)

            xs = (xsr.replace('-', '')
                     .replace('\' ', '\'')
                     .replace('  ', ' ')
                     .replace('#', 'nC'))

            dictf.write((u'%s %s\n' % (token, xs)).encode('utf8'))

            for p in xs.split(' '):

                if len(p) < 1:
                    logging.error(
                        u"****ERROR: empty phoneme in : '%s' ('%s', ipa: '%s', token: '%s')" % (
                        xs, xsr, ipa, token))

                pws = p[1:] if p[0] == '\'' else p

                if not pws in ps:
                    ps[pws] = {p}
                else:
                    ps[pws].add(p)
    logging.info("%s written." % dictfn2)
    logging.info("Exporting dictionary ... done.")

    return ps, utt_dict


def write_nonsilence_phones(ps, psfn):
    with open(psfn, 'w') as psf:
        for pws in ps:
            for p in sorted(list(ps[pws])):
                psf.write((u'%s ' % p).encode('utf8'))

            psf.write('\n')
    logging.info('%s written.' % psfn)


def write_silence_phones(psfn):
    with open(psfn, 'w') as psf:
        psf.write('SIL\nSPN\nNSN\n')
    logging.info('%s written.' % psfn)


def write_optional_silence(psfn):
    with open(psfn, 'w') as psf:
        psf.write('SIL\n')
    logging.info('%s written.' % psfn)


def write_extra_questions(ps, psfn):
    with open(psfn, 'w') as psf:
        psf.write('SIL SPN NSN\n')

        for pws in ps:
            for p in ps[pws]:
                if '\'' in p:
                    continue
                psf.write((u'%s ' % p).encode('utf8'))
        psf.write('\n')

        for pws in ps:
            for p in ps[pws]:
                if not '\'' in p:
                    continue
                psf.write((u'%s ' % p).encode('utf8'))

        psf.write('\n')
    logging.info('%s written.' % psfn)


def create_training_data_for_language_model(transcript_objs, utt_dict, data_dir):
    transcripts = {}
    for transcript_obj in transcript_objs:
        transcripts.update(transcript_obj.ts)
    misc.mkdirs('%s/local/lm' % data_dir)
    fn = '%s/local/lm/train_nounk.txt' % data_dir
    with open(fn, 'w') as f:

        for utt_id in sorted(transcripts):
            ts = transcripts[utt_id]
            f.write((u'%s\n' % ts['ts']).encode('utf8'))
    logging.info("%s written." % fn)
    fn = '%s/local/lm/wordlist.txt' % data_dir
    with open(fn, 'w') as f:

        for token in sorted(utt_dict):
            f.write((u'%s\n' % token).encode('utf8'))
    logging.info("%s written." % fn)


def copy_scripts_and_config_files(work_dir, kaldi_root):
    misc.copy_file('data/src/speech/kaldi-run-chain.sh',           '%s/run-chain.sh' % work_dir)
    misc.copy_file('data/src/speech/kaldi-run-adapt-lm.sh',        '%s/run-adapt-lm.sh' % work_dir)
    misc.copy_file('data/src/speech/kaldi-cmd.sh',                 '%s/cmd.sh' % work_dir)
    misc.render_template('data/src/speech/kaldi-path.sh.template', '%s/path.sh' % work_dir, kaldi_root=kaldi_root)
    misc.mkdirs('%s/conf' % work_dir)
    misc.copy_file('data/src/speech/kaldi-mfcc.conf',              '%s/conf/mfcc.conf' % work_dir)
    misc.copy_file('data/src/speech/kaldi-mfcc-hires.conf',        '%s/conf/mfcc_hires.conf' % work_dir)
    misc.copy_file('data/src/speech/kaldi-online-cmvn.conf',       '%s/conf/online_cmvn.conf' % work_dir)
    misc.mkdirs('%s/local' % work_dir)
    misc.copy_file('data/src/speech/kaldi-score.sh',               '%s/local/score.sh' % work_dir)
    misc.mkdirs('%s/local/nnet3' % work_dir)
    misc.copy_file('data/src/speech/kaldi-run-ivector-common.sh',  '%s/local/nnet3/run_ivector_common.sh' % work_dir)

misc.init_app('speech_kaldi_export')

#
# commandline
#

parser = OptionParser("usage: %prog [options] <model_name> <dictionary> <language_model> <audio_corpus> [ <audio_corpus2> ... ]")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0, help="Limit number of sentences (debug purposes only), default: 0")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")

parser.add_option ("-s", "--sequitur-model", dest="sequitur_model", type='str', 
                   help="sequitur model (used to generate missing dict entries, if given)")

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

work_dir = '%s/kaldi/%s' % (ASR_MODELS_DIR, model_name)
data_dir = '%s/data' % work_dir
mfcc_dir = '%s/mfcc' % work_dir

if options.sequitur_model:
    sequitur_model_path = '%s/%s' % (SEQUITUR_MODEL_DIR, options.sequitur_model)
else:
    sequitur_model_path = None

#
# config
#

config = misc.load_config ('.speechrc')

kaldi_root = config.get("speech", "kaldi_root")
wav16_dir  = config.get("speech", "wav16")

#
# create basic work dir structure
#

# FIXME: unused, remove misc.mkdirs('%s/lexicon' % data_dir)
misc.mkdirs('%s/local/dict' % data_dir)
misc.mkdirs(wav16_dir)
misc.mkdirs(mfcc_dir)
misc.symlink('../../../../../%s' % language_model_dir, '%s/lm' % work_dir)
misc.symlink('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % work_dir)
misc.symlink('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % work_dir)

#
# generate speech and text corpora
#

logging.info("loading lexicon...")
lex = Lexicon(file_name=dictionary)
logging.info("loading lexicon...done.")

if sequitur_model_path:
    add_all = True
else:
    add_all = False

ts_all = {}
ts_train = {}
ts_test = {}
transcript_objs = []
for audio_corpus in audio_corpora:

    logging.info("loading transcripts from %s ..." % audio_corpus)

    transcripts = Transcripts(corpus_name=audio_corpus)

    ts_all_, ts_train_, ts_test_ = transcripts.split(limit=options.debug, add_all=add_all, lang=options.lang)

    ts_all.update(ts_all_)
    ts_train.update(ts_train_)
    ts_test.update(ts_test_)
    transcript_objs.append(transcripts)

    logging.info("loading transcripts from %s: %d train, %d test samples." % (audio_corpus, len(ts_train_), len(ts_test_)))

logging.info("loading transcripts done, total: %d train, %d test samples." % (len(ts_train), len(ts_test)))

export_kaldi_data(wav16_dir, audio_corpora, '%s/train/' % data_dir, ts_train)
export_kaldi_data(wav16_dir, audio_corpora, '%s/test/' % data_dir, ts_test)

#
# export dict
#

if sequitur_model_path:
    for transcript_obj in transcript_objs:
        lex = add_missing_words(transcript_obj, lex, sequitur_model_path)

ps, utt_dict = export_dictionary(ts_all,
                                 lex,
                                 '%s/local/dict/lexicon.txt' % data_dir,
                                 options.prompt_words)

#
# phones etc
#

write_nonsilence_phones(ps, '%s/local/dict/nonsilence_phones.txt' % data_dir)

write_silence_phones('%s/local/dict/silence_phones.txt' % data_dir)
write_optional_silence('%s/local/dict/optional_silence.txt' % data_dir)
write_extra_questions(ps, '%s/local/dict/extra_questions.txt' % data_dir)
create_training_data_for_language_model(transcript_objs, utt_dict, data_dir)

#
# script
#

copy_scripts_and_config_files(work_dir, kaldi_root)

logging.info ( "All done." )

