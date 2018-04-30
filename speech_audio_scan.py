#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Marc Puels
# Copyright 2016, 2017 Guenter Bartsch
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
# Scan directory for audio files and convert them to wav files
#
# For each speech corpus `speech_corpus`
#
# 1. the resulting wav files are written to the directory
#    `.speechrc.wav16`/<speech_corpus>/
#
# 2. the transcripts in data/src/speech/<speech_corpus>/transcripts_*.csv are
#    updated.
#

import os
import sys
import logging

import plac
from pathlib2 import Path

from nltools import misc
from speech_transcripts import Transcripts


SPEECH_CORPORA = [
    "forschergeist",
    "gspv2",
    "librivox",
    "voxforge_de",
    "voxforge_en",
    "zamia_de",
]


@plac.annotations(
    verbose=("Enable verbose logging", "flag", "v"),
    speech_corpora=("Name of the speech corpus to scan. Allowed values: "
                    + ", ".join(SPEECH_CORPORA), "positional", None, str, None,
                    "speech_corpus"))
def main(verbose=False, *speech_corpora):
    """Scan directory for audio files and convert them to wav files

    For each speech corpus `speech_corpus`

    1. the resulting wav files are written to the directory
       `.speechrc.wav16`/<speech_corpus>/

    2. the transcripts in data/src/speech/<speech_corpus>/transcripts_*.csv are
       updated.
    """
    misc.init_app('speech_audio_scan')

    config = misc.load_config('.speechrc')

    speech_corpora_dir = Path(config.get("speech", "speech_corpora"))
    wav16 = Path(config.get("speech", "wav16"))

    if len(speech_corpora) < 1:
        logging.error("At least one speech corpus must be provided.")
        sys.exit(1)

    for speech_corpus in speech_corpora:
        if speech_corpus not in SPEECH_CORPORA:
            logging.error("Unsupported corpus: " + speech_corpus)
            sys.exit(1)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    exit_if_corpus_is_missing(speech_corpora_dir, speech_corpora)

    for speech_corpus in speech_corpora:
        transcripts = Transcripts(corpus_name=speech_corpus)
        out_wav16_subdir = wav16 / speech_corpus
        out_wav16_subdir.mkdir(parents=True, exist_ok=True)
        in_root_corpus_dir = speech_corpora_dir / speech_corpus

        scan_audiodir(str(in_root_corpus_dir),
                      transcripts,
                      str(out_wav16_subdir))

        transcripts.save()
        print speech_corpus, "new transcripts saved."
        print


def exit_if_corpus_is_missing(speech_corpora_dir, speech_corpora):
    missing_directories = []
    for speech_corpus in speech_corpora:
        corpus_dir = speech_corpora_dir / speech_corpus
        if not corpus_dir.is_dir():
            missing_directories.append(str(corpus_dir))

    if missing_directories:
        logging.error(
            "Could not find the following directories. Please update the var "
            "`speech_corpora` in ~/.speechrc or move the missing corpus under "
            "the directory set by `speech_corpora`. Missing directories: " +
            ", ".join(missing_directories))
        sys.exit(1)


def scan_audiodir(audiodir, transcripts, out_wav16_subdir):

    # keep track of all cfns we have audio files for
    cfn_audio = set()

    for subdir in os.listdir(audiodir):

        if not '-' in subdir:
            logging.warn('skipping %s as it does not match our naming scheme' % subdir)
            continue

        logging.debug ("scanning %s in %s" % (subdir, audiodir))

        subdirfn  = '%s/%s'   % (audiodir, subdir)
        wavdirfn  = '%s/wav'  % subdirfn
        flacdirfn = '%s/flac' % subdirfn

        # do we have prompts?

        prompts = {}

        promptsfn = '%s/etc/prompts-original' % subdirfn
        if os.path.isfile(promptsfn):
            with open(promptsfn) as promptsf:
                while True:
                    line = promptsf.readline().decode('utf8', errors='ignore')
                    if not line:
                        break

                    line = line.rstrip()
                    if '\t' in line:
                        afn = line.split('\t')[0]
                        ts = line[len(afn)+1:]
                    else:
                        afn = line.split(' ')[0]
                        ts = line[len(afn)+1:]

                    prompts[afn] = ts.replace(';',',')

            # print repr(prompts)

        for audiodirfn in [wavdirfn, flacdirfn]:

            if not os.path.isdir(audiodirfn):
                continue

            for audiofullfn in os.listdir(audiodirfn):

                audiofn = audiofullfn.split('.')[0]
                cfn = '%s_%s' % (subdir, audiofn)
                cfn_audio.add(cfn)

                if not cfn in transcripts:
                    # print repr(prompts)
                    prompt = prompts[audiofn] if audiofn in prompts else ''

                    logging.info ("new audio found: %s %s %s" % (cfn, audiofn, prompt))

                    spk     = cfn.split('-')[0]

                    v = { 'dirfn'   : os.path.basename(os.path.normpath(subdirfn)),
                          'audiofn' : audiofn,
                          'prompt'  : prompt,
                          'ts'      : '',
                          'quality' : 0,
                          'spk'     : spk}

                    transcripts[cfn] = v

                audio_convert (cfn, subdir, audiofn, audiodir, out_wav16_subdir)

    # report missing audio files
    for cfn in sorted(transcripts):
        if cfn in cfn_audio:
            continue
        logging.warn('audio file missing for %s' % cfn)


def audio_convert(cfn, subdir, fn, audiodir, wav16_dir):
    # global mfcc_dir

    # convert audio if not done yet

    w16filename = "%s/%s.wav" % (wav16_dir, cfn)

    if not os.path.isfile(w16filename):

        wavfilename = "%s/%s/wav/%s.wav" % (audiodir, subdir, fn)

        if not os.path.isfile(wavfilename):
            # flac ?
            flacfilename = "%s/%s/flac/%s.flac" % (audiodir, subdir, fn)

            if not os.path.isfile(flacfilename):
                print "   WAV file '%s' does not exist, neither does FLAC file '%s' => skipping submission." % (
                wavfilename, flacfilename)
                return False

            print "%-20s: converting %s => %s (16kHz mono)" % (
            cfn, flacfilename, w16filename)
            os.system(
                "sox '%s' -r 16000 -b 16 -c 1 %s" % (flacfilename, w16filename))

        else:

            print "%-20s: converting %s => %s (16kHz mono)" % (
            cfn, wavfilename, w16filename)
            os.system(
                "sox '%s' -r 16000 -b 16 -c 1 %s" % (wavfilename, w16filename))

    return True


if __name__ == "__main__":
    plac.call(main)
