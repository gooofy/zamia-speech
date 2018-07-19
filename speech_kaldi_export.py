#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Copyright 2018 Marc Puels
# Copyright 2016, 2017, 2018 Guenter Bartsch
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
from pathlib2 import Path

import plac

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa
from nltools.sequiturclient import sequitur_gen_ipa

from speech_lexicon     import Lexicon
from speech_transcripts import Transcripts

from paths import ASR_MODELS_DIR, LANGUAGE_MODELS_DIR

SEQUITUR_MODEL_DIR = Path('data/models/sequitur')

@plac.annotations(
    model_name="The name of the resulting speech recognition system. All files "
               "belonging to the experiment will be written to the "
               "directory data/dst/asr-models/<model_name>/.",
    dictionary="The pronunciation dictionary to use. Valid values are the "
               "names of the files in data/src/dicts/.",
    language_model="The language model to use. Valid values are the names of "
                   "the directories in data/dst/lm/.",
    sequitur_model=("Name of a sequitur model. Valid values are the names of "
                    "the files in data/models/sequitur/. If a name is given, "
                    "then missing entries in the pronunciation dictionary will "
                    "be automaticially generated with the sequitur model.",
                    "option", "s", str),
    debug=("Limit number of sentences (debug purposes only), default: 0 "
           "(unlimited)", "option", "d", int),
    verbose=("Enable verbose logging", "flag", "v"),
    prompt_words=("Limit dict to tokens covered in prompts", "flag", "p"),
    audio_corpora=("The audio corpora to train the acoustic model on.",
                   "positional", None, None, None, "audio_corpus"))
def main(model_name, dictionary, language_model, sequitur_model=None, debug=0,
         verbose=False, prompt_words=False, *audio_corpora):

    misc.init_app('speech_kaldi_export')

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    language_model_dir = LANGUAGE_MODELS_DIR.resolve() / language_model
    exit_if_language_model_dir_doesnt_exist(language_model_dir)

    config = misc.load_config ('.speechrc')

    work_dir = ASR_MODELS_DIR / 'kaldi' / model_name
    kaldi_root = config.get("speech", "kaldi_root")

    data_dir = work_dir / "data"
    mfcc_dir = work_dir / "mfcc"

    wav16_dir = config.get("speech", "wav16")

    create_basic_work_dir_structure(
        str(data_dir),
        wav16_dir,
        str(mfcc_dir),
        str(work_dir),
        str(language_model_dir),
        kaldi_root)

    if sequitur_model:
        sequitur_model_path = str(SEQUITUR_MODEL_DIR / sequitur_model)
    else:
        sequitur_model_path = None

    generate_speech_and_text_corpora(data_dir,
                                     wav16_dir,
                                     debug,
                                     sequitur_model_path,
                                     dictionary,
                                     audio_corpora,
                                     prompt_words)

    copy_scripts_and_config_files(work_dir, kaldi_root)


def exit_if_language_model_dir_doesnt_exist(language_model_dir):
    if not language_model_dir.is_dir():
        logging.error(
            "Could not find language model directory {}. Create a language "
            "model first with speech_build_lm.py.".format(language_model_dir))
        sys.exit(1)


def create_basic_work_dir_structure(data_dir, wav16_dir, mfcc_dir, work_dir,
                                    language_model_dir, kaldi_root):
    # FIXME: unused, remove misc.mkdirs('%s/lexicon' % data_dir)
    misc.mkdirs('%s/local/dict' % data_dir)
    misc.mkdirs(wav16_dir)
    misc.mkdirs(mfcc_dir)
    misc.symlink(language_model_dir, '%s/lm' % work_dir)
    misc.symlink('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % work_dir)
    misc.symlink('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % work_dir)


def generate_speech_and_text_corpora(data_dir,
                                     wav16_dir,
                                     debug,
                                     sequitur_model_path,
                                     lexicon_file_name,
                                     audio_corpora,
                                     prompt_words):
    logging.info("loading lexicon...")
    lex = Lexicon(file_name=lexicon_file_name)
    logging.info("loading lexicon...done.")
    logging.info("loading transcripts...")

    if sequitur_model_path:
        add_all = True
    else:
        add_all = False

    ts_all = {}
    ts_train = {}
    ts_test = {}
    transcript_objs = []
    for audio_corpus in audio_corpora:
        transcripts = Transcripts(corpus_name=audio_corpus)

        ts_all_, ts_train_, ts_test_ = transcripts.split(limit=debug, add_all=add_all)

        logging.info("loading transcripts from %s (%d train, %d test) ..." % (audio_corpus, len(ts_train_), len(ts_test_)))

        ts_all.update(ts_all_)
        ts_train.update(ts_train_)
        ts_test.update(ts_test_)
        transcript_objs.append(transcripts)

    logging.info("loading transcripts (%d train, %d test) ...done." % (
        len(ts_train), len(ts_test)))

    export_kaldi_data(wav16_dir, audio_corpora, '%s/train/' % data_dir, ts_train)
    export_kaldi_data(wav16_dir, audio_corpora, '%s/test/' % data_dir, ts_test)

    if sequitur_model_path:
        for transcript_obj in transcript_objs:
            lex = add_missing_words(transcript_obj, lex, sequitur_model_path)

    ps, utt_dict = export_dictionary(ts_all,
                                     lex,
                                     '%s/local/dict/lexicon.txt' % data_dir,
                                     prompt_words)
    write_nonsilence_phones(
        ps, '%s/local/dict/nonsilence_phones.txt' % data_dir)

    write_silence_phones('%s/local/dict/silence_phones.txt' % data_dir)
    write_optional_silence('%s/local/dict/optional_silence.txt' % data_dir)
    write_extra_questions(ps, '%s/local/dict/extra_questions.txt' % data_dir)
    create_training_data_for_language_model(transcript_objs, utt_dict, data_dir)


def export_kaldi_data (wav16_dir, audio_corpora, destdirfn, tsdict):
    logging.info ( "Exporting to %s..." % destdirfn)

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

    # concat_sort_write(
    #     ['data/src/speech/%s/spk2gender' % audio_corpus
    #      for audio_corpus in audio_corpora],
    #     '%s/spk2gender' % destdirfn)


def concat_sort_write(src_paths, dst_path):
    lines = []
    for src_path in src_paths:
        with open(src_path) as f:
            lines += [line for line in f]

    with open(dst_path, "wt") as f:
        for line in sorted(lines):
            f.write(line)


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

        for word in tokenize(ts['prompt']):
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
                        u"****ERROR: empty phoneme in : '%s' ('%s', ipa: '%s')" % (
                        xs, xsr, ipa))

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
    misc.copy_file('data/src/speech/kaldi-run-lm.sh', '%s/run-lm.sh' % work_dir)
    # misc.copy_file ('data/src/speech/kaldi-run-am.sh', '%s/run-am.sh' % work_dir)
    # misc.copy_file ('data/src/speech/kaldi-run-nnet3.sh', '%s/run-nnet3.sh' % work_dir)
    misc.copy_file('data/src/speech/kaldi-run-chain.sh',
                   '%s/run-chain.sh' % work_dir)
    # misc.copy_file('data/src/speech/kaldi-run-chain-wrapper.sh',
    #                '%s/run-chain-wrapper.sh' % work_dir)
    # misc.copy_file('data/src/speech/kaldi-run-chain-cfg.sh',
    #                '%s/run-chain-cfg.sh' % work_dir)
    # misc.copy_file('data/src/speech/kaldi-run-chain-cpu.sh',
    #                '%s/run-chain-cpu.sh' % work_dir)
    # misc.copy_file('data/src/speech/kaldi-run-chain-cpu-wrapper.sh',
    #                '%s/run-chain-cpu-wrapper.sh' % work_dir)
    # misc.copy_file('data/src/speech/kaldi-run-chain-gpu.sh',
    #                '%s/run-chain-gpu.sh' % work_dir)
    # misc.copy_file('data/src/speech/kaldi-run-chain-gpu-wrapper.sh',
    #                '%s/run-chain-gpu-wrapper.sh' % work_dir)
    misc.copy_file('data/src/speech/kaldi-cmd.sh', '%s/cmd.sh' % work_dir)
    misc.render_template('data/src/speech/kaldi-path.sh.template',
                         '%s/path.sh' % work_dir, kaldi_root=kaldi_root)
    misc.mkdirs('%s/conf' % work_dir)
    misc.copy_file('data/src/speech/kaldi-mfcc.conf',
                   '%s/conf/mfcc.conf' % work_dir)
    misc.copy_file('data/src/speech/kaldi-mfcc-hires.conf',
                   '%s/conf/mfcc_hires.conf' % work_dir)
    misc.copy_file('data/src/speech/kaldi-online-cmvn.conf',
                   '%s/conf/online_cmvn.conf' % work_dir)
    misc.mkdirs('%s/local' % work_dir)
    misc.copy_file('data/src/speech/kaldi-score.sh',
                   '%s/local/score.sh' % work_dir)
    misc.mkdirs('%s/local/nnet3' % work_dir)
    misc.copy_file('data/src/speech/kaldi-run-ivector-common.sh',
                   '%s/local/nnet3/run_ivector_common.sh' % work_dir)


if __name__ == "__main__":
    plac.call(main)
    logging.info ( "All done." )

