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

from nltools            import misc
from speech_transcripts import Transcripts
from optparse           import OptionParser

PROC_TITLE = 'speech_audio_scan'

def exit_if_corpus_is_missing(speech_corpora_dir, speech_corpora):

    missing_directories = []
    for speech_corpus in speech_corpora:
        corpus_dir = '%s/%s' % (speech_corpora_dir, speech_corpus)
        if not os.path.isdir(corpus_dir):
            missing_directories.append(corpus_dir)

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

                audiofn = os.path.splitext(audiofullfn)[0]
                cfn = '%s_%s' % (subdir, audiofn)
                cfn_audio.add(cfn)

                if not cfn in transcripts:
                    # import pdb; pdb.set_trace()

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
# @plac.annotations(
#     verbose=("Enable verbose logging", "flag", "v"),
#     speech_corpora=("Name of the speech corpus to scan. Example values: "
#                     + ", ".join(SPEECH_CORPORA), "positional", None, str, None,
#                     "speech_corpus"))

    misc.init_app(PROC_TITLE)

    #
    # config
    #

    config = misc.load_config('.speechrc')

    speech_corpora_dir = config.get("speech", "speech_corpora")
    wav16              = config.get("speech", "wav16")

    speech_corpora_available = []
    for corpus in os.listdir(speech_corpora_dir):
        if not os.path.isdir('%s/%s' % (speech_corpora_dir, corpus)):
            continue
        speech_corpora_available.append(corpus)

    #
    # commandline
    #

    parser = OptionParser("usage: %%prog [options] <speech_corpora>\n  speech_corpora: one or more of %s" % ", ".join(speech_corpora_available))

    parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                       help="verbose output")

    (options, speech_corpora) = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if len(speech_corpora) < 1:
        logging.error("At least one speech corpus must be provided.")
        sys.exit(1)

    exit_if_corpus_is_missing(speech_corpora_dir, speech_corpora)

    for speech_corpus in speech_corpora:
        transcripts = Transcripts(corpus_name=speech_corpus, create_db=True)
        out_wav16_subdir = '%s/%s' % (wav16, speech_corpus)
        misc.mkdirs(out_wav16_subdir)
        in_root_corpus_dir = '%s/%s' % (speech_corpora_dir, speech_corpus)

        scan_audiodir(str(in_root_corpus_dir), transcripts, str(out_wav16_subdir))

        transcripts.save()

        print speech_corpus, "new transcripts saved."
        print

