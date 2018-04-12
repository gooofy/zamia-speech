#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
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
# retrieve segmentation results from kaldi, produce voxforge
# directory structure containing prompts and wavs
#

import os
import sys
import logging
import traceback
import codecs
import wave, struct, array

import numpy as np

from optparse import OptionParser

from nltools                import misc

WORKDIR          = 'data/dst/speech/de/kaldi'

SAMPLE_RATE      = 16000

#
# init 
#

misc.init_app ('abook-kaldi-retrieve')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] srcdir")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

srcdirfn = args[0]

#
# read wavs
#

wavdict = {}

for fn in os.listdir(srcdirfn):

    if not fn.endswith('.wav'):
        continue

    wavfn = '%s/%s' % (srcdirfn, fn)
    wav_id = os.path.splitext(fn)[0]

    wavf = wave.open(wavfn, 'r')
    length = wavf.getnframes()
    sr     = wavf.getframerate()

    logging.info ('reading %s (%d samples, %d samples/s, %fs)...' % (fn, length, sr, float(length)/float(sr)))

    if sr != SAMPLE_RATE:
        logging.error ('%s: expected sample rate: %d, found:%d' % (inputfn, SAMPLE_RATE, sr))
        sys.exit(2)

    wd = wavf.readframes(length)
    samples = np.fromstring(wd, dtype=np.int16)

    wavdict[wav_id] = samples

#
# read prompts
#

promptsdict = {}

promptfn = '%s/data/segmentation_result_a_cleaned_b/text' % WORKDIR

with codecs.open(promptfn, 'r', 'utf8') as promptf:

    for line in promptf:
        parts = line.strip().split(u" ")

        promptsdict[parts[0]] = u" ".join(parts[1:])

logging.info ('read %s : %d segments.' % (promptfn, len(promptsdict)))

#
# extract segments
#

segmentsfn = '%s/data/segmentation_result_a_cleaned_b/segments' % WORKDIR

segcnt = 0

with codecs.open(segmentsfn, 'r', 'utf8') as segmentsf:

    for line in segmentsf:
        parts = line.strip().split(u" ")

        if len(parts) != 4:
            logging.error ('%s: failed to parse line: %s' % (segmentsfn, line))

        seg_id     = parts[0]
        wavfn      = parts[1]
        wav_id     = os.path.basename(wavfn)
        seg_start  = float(parts[2])
        seg_end    = float(parts[3])

        #
        # create output dir structure if it doesn't exist
        #

        outdirfn = 'abook/out/%s' % os.path.basename(wav_id)

        if not os.path.exists(outdirfn):
            logging.info ('creating %s ...' % outdirfn)
            misc.mkdirs(outdirfn)
            misc.mkdirs('%s/etc' % outdirfn)
            misc.mkdirs('%s/wav' % outdirfn)

        #
        # prompt
        #

        uid = 'de5-%06d' % segcnt
        segcnt += 1

        prompt    = promptsdict[seg_id]
        promptsfn = '%s/etc/prompts-original' % outdirfn
        with codecs.open (promptsfn, 'a', 'utf8') as promptsf:
            promptsf.write(u'%s %s\n' % (uid, prompt))


        #
        # create wave file
        #

        s_start = int(seg_start * SAMPLE_RATE)
        s_end   = int(seg_end * SAMPLE_RATE)

        segment_samples = []
        for s in wavdict[wav_id][s_start:s_end]:
            segment_samples.append(s)

        wavoutfn  = "%s/wav/%s.wav" % (outdirfn, uid)

        wavoutf   = wave.open(wavoutfn, 'w')
        wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))

        A = array.array('h', segment_samples)
        wd = A.tostring()
        wavoutf.writeframes(wd)
        wavoutf.close()

        seconds = float(len(segment_samples)) / float(SAMPLE_RATE)
        logging.info ('segment [%7d:%7d] %s written, %5.1fs.' % (s_start, s_end, wavoutfn, seconds))

sys.exit(0)


wavfn = os.path.abspath(args[0])

speaker = 'segspeaker'
utt_id = os.path.splitext(wavfn)[0]

transcriptfn = args[1]

#
# config
#

kaldi_root  = config.get("speech", "kaldi_root")

data_dir    = "%s/data" % WORKDIR
mfcc_dir    = "%s/mfcc" % WORKDIR

#
# load lexicon, transcripts
#

# logging.info ( "loading lexicon...")
# lex = Lexicon(lang=options.lang)
# logging.info ( "loading lexicon...done.")

#
# load transcript, tokenize
#

tokens = []
with codecs.open (transcriptfn, 'r', 'utf8') as transcriptf:
    for line in transcriptf:
        for token in tokenize(line):
            tokens.append(token)
transcript = u" ".join(tokens)

#
# create work_dir structure
#

# misc.mkdirs('%s/local/dict' % data_dir)

#
# kaldi data part
#

destdirfn = '%s/segmentation/' % data_dir

logging.info ( "Exporting to %s..." % destdirfn)

misc.mkdirs(destdirfn)

with open(destdirfn+'wav.scp','w') as wavscpf,  \
     open(destdirfn+'utt2spk','w') as utt2spkf, \
     codecs.open(destdirfn+'text','w', 'utf8') as textf, \
     open(destdirfn+'spk2gender','w') as spk2genderf:

    textf.write(u'%s %s\n' % (utt_id, transcript))

    wavscpf.write('%s %s\n' % (utt_id, wavfn))

    utt2spkf.write('%s %s\n' % (utt_id, speaker))

    spk2genderf.write('%s m\n' % speaker)

sys.exit(0)

#
# dictionary export
#

dictfn2 = '%s/local/dict/lexicon.txt' % data_dir

logging.info ( "Exporting dictionary..." )

utt_dict = {}

if options.prompt_words:
    for ts in ts_all:

        tsd = ts_all[ts]

        tokens = tsd['ts'].split(' ')

        # logging.info ( '%s %s' % (repr(ts), repr(tokens)) )

        for token in tokens:
            if token in utt_dict:
                continue

            if not token in lex.dictionary:
                logging.error ( "*** ERROR: missing token in dictionary: '%s' (tsd=%s, tokens=%s)" % (token, repr(tsd), repr(tokens)) )
                sys.exit(1)

            utt_dict[token] = lex.dictionary[token]['ipa']

else:

    for token in lex:
        utt_dict[token] = lex.dictionary[token]['ipa']

ps = {}

with open (dictfn2, 'w') as dictf:

    dictf.write('!SIL SIL\n')

    for token in sorted(utt_dict):

        ipa = utt_dict[token]
        xsr = ipa2xsampa (token, ipa, spaces=True)

        xs = xsr.replace('-','').replace('\' ', '\'').replace('  ', ' ').replace('#', 'nC')

        dictf.write((u'%s %s\n' % (token, xs)).encode('utf8'))

        for p in xs.split(' '):

            if len(p)<1:
                logging.error ( u"****ERROR: empty phoneme in : '%s' ('%s', ipa: '%s', token: '%s')" % (xs, xsr, ipa, token) )

            pws = p[1:] if p[0] == '\'' else p

            if not pws in ps:
                ps[pws] = set([p])
            else:
                ps[pws].add(p)

logging.info ( "%s written." % dictfn2 )

logging.info ( "Exporting dictionary ... done." )

#
# phoneme sets
#

# logging.info ( "Phoneme set: %s" % repr(ps) )

psfn = '%s/local/dict/nonsilence_phones.txt' % data_dir
with open(psfn, 'w') as psf:
    for pws in sorted(ps):
        for p in sorted(list(ps[pws])):
            psf.write((u'%s ' % p).encode('utf8'))

        psf.write('\n')

logging.info ( '%s written.' % psfn )

psfn = '%s/local/dict/silence_phones.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\nSPN\nNSN\n')
logging.info ( '%s written.' % psfn )

psfn = '%s/local/dict/optional_silence.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\n')
logging.info ( '%s written.' % psfn )

psfn = '%s/local/dict/extra_questions.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL SPN NSN\n')

    for pws in sorted(ps):
        for p in sorted(list(ps[pws])):
            if '\'' in p:
                continue
            psf.write((u'%s ' % p).encode('utf8'))
    psf.write('\n')

    for pws in sorted(ps):
        for p in sorted(list(ps[pws])):
            if not '\'' in p:
                continue
            psf.write((u'%s ' % p).encode('utf8'))

    psf.write('\n')

logging.info ( '%s written.' % psfn )

#
# language model
#

misc.mkdirs ('%s/local/lm' % data_dir)

fn = '%s/local/lm/train_nounk.txt' % data_dir

with open(fn, 'w') as f:
    
    for utt_id in sorted(transcripts):
        ts = transcripts[utt_id]
        f.write((u'%s\n' % ts['ts']).encode('utf8'))

logging.info ( "%s written." % fn )

fn = '%s/local/lm/wordlist.txt' % data_dir

with open(fn, 'w') as f:
    
    for token in sorted(utt_dict):
        f.write((u'%s\n' % token).encode('utf8'))

logging.info ( "%s written." % fn )

#
# copy scripts and config files
#

misc.copy_file ('data/src/speech/kaldi-run-lm.sh', '%s/run-lm.sh' % work_dir)
# misc.copy_file ('data/src/speech/kaldi-run-am.sh', '%s/run-am.sh' % work_dir)
# misc.copy_file ('data/src/speech/kaldi-run-nnet3.sh', '%s/run-nnet3.sh' % work_dir)
misc.copy_file ('data/src/speech/kaldi-run-chain.sh', '%s/run-chain.sh' % work_dir)
misc.copy_file ('data/src/speech/kaldi-cmd.sh', '%s/cmd.sh' % work_dir)
misc.copy_file ('data/src/speech/kaldi-path.sh', '%s/path.sh' % work_dir)
misc.mkdirs ('%s/conf' % work_dir)
misc.copy_file ('data/src/speech/kaldi-mfcc.conf', '%s/conf/mfcc.conf' % work_dir)
misc.copy_file ('data/src/speech/kaldi-mfcc-hires.conf', '%s/conf/mfcc_hires.conf' % work_dir)
misc.copy_file ('data/src/speech/kaldi-online-cmvn.conf', '%s/conf/online_cmvn.conf' % work_dir)
misc.mkdirs ('%s/local' % work_dir)
misc.copy_file ('data/src/speech/kaldi-score.sh', '%s/local/score.sh' % work_dir)
misc.mkdirs ('%s/local/nnet3' % work_dir)
misc.copy_file ('data/src/speech/kaldi-run-ivector-common.sh', '%s/local/nnet3/run_ivector_common.sh' % work_dir)

#
# main
#

logging.info ( "All done." )

