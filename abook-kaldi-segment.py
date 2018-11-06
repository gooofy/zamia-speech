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
# create a kaldi long audio segmentation experiment
# based on work by Vimal Manohar 
#
# references: 
# - https://github.com/kaldi-asr/kaldi/pull/1167
# - kaldi: tedlium/s5_r2/local/run_segmentation_long_utts.sh 
#

import os
import sys
import logging
import traceback
import codecs

from optparse import OptionParser

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa

from speech_lexicon     import Lexicon
# from speech_transcripts import Transcripts

WORKDIR          = 'data/dst/asr-models/kaldi/segmentation'

#
# init 
#

misc.init_app ('abook_kaldi_segment')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] model srcdir")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 2:
    parser.print_usage()
    sys.exit(1)

modelfn  = args[0]
srcdirfn = args[1]

#
# config
#

kaldi_root  = config.get("speech", "kaldi_root")

#
# clean up leftovers from previous runs
#

cmd = 'rm -rf %s' % WORKDIR
logging.info(cmd)
os.system(cmd)
misc.mkdirs(WORKDIR)

#
# copy scripts
#

misc.copy_file ('data/src/speech/kaldi-run-segmentation.sh', '%s/run-segmentation.sh' % WORKDIR)

misc.copy_file ('data/src/speech/kaldi-cmd.sh', '%s/cmd.sh' % WORKDIR)
misc.render_template ('data/src/speech/kaldi-path.sh.template', '%s/path.sh' % WORKDIR, kaldi_root=kaldi_root)
misc.symlink ('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % WORKDIR)
misc.symlink ('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % WORKDIR)

#
# create skeleton dst model
#

misc.mkdirs ('%s/exp'  % WORKDIR)

cmd = "cp -r '%s/model' '%s/exp/tri2b_adapt'" % (modelfn, WORKDIR)
logging.info(cmd)
os.system(cmd)
cmd = "cp -r '%s/data'  '%s/data'" % (modelfn, WORKDIR)
logging.info(cmd)
os.system(cmd)
cmd = "cp -r '%s/conf'  '%s/conf'" % (modelfn, WORKDIR)
logging.info(cmd)
os.system(cmd)

#
# kaldi data for segmentation
#

data_dir    = "%s/data" % WORKDIR

destdirfn = '%s/segmentation/' % data_dir

logging.info ("exporting to %s ..." % destdirfn)

misc.mkdirs(destdirfn)

speakers = set()
promptsfns = []
for fn in os.listdir(srcdirfn):
    if not fn.endswith('.prompt'):
        continue
    promptsfns.append(fn)

with open(destdirfn+'wav.scp','w') as wavscpf,  \
     open(destdirfn+'utt2spk','w') as utt2spkf, \
     codecs.open(destdirfn+'text','w', 'utf8') as textf:

    for fn in sorted(promptsfns):

        transcriptfn = '%s/%s' % (srcdirfn, fn)
        wavfn        = '%s/%s.wav' % (os.path.abspath(srcdirfn), os.path.splitext(fn)[0])

        parts = os.path.splitext(fn)[0].split('-')

        speaker = parts[0]
        speakers.add(speaker)

        utt_id = os.path.splitext(fn)[0]

        #
        # load transcript, tokenize
        #

        tokens = []
        with codecs.open (transcriptfn, 'r', 'utf8') as transcriptf:
            for line in transcriptf:
                for token in tokenize(line):
                    tokens.append(token)
        transcript = u" ".join(tokens)

        textf.write(u'%s %s\n' % (utt_id, transcript))

        wavscpf.write('%s %s\n' % (utt_id, wavfn))

        utt2spkf.write('%s %s\n' % (utt_id, speaker))

with open(destdirfn+'spk2gender','w') as spk2genderf:
    for speaker in sorted(list(speakers)):
        spk2genderf.write('%s m\n' % speaker)

sys.exit(0)


#
# create adaptation case
#

misc.mkdirs('%s/local/dict.adapt' % data_dir)

dictfn2 = '%s/local/dict.adapt/lexicon.txt' % data_dir

logging.info ( "Exporting dictionary..." )

ps = {}

with open (dictfn2, 'w') as dictf:

    dictf.write('!SIL SIL\n')

    for token in sorted(lex):

        ipa = lex[token]['ipa']
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

psfn = '%s/local/dict.adapt/nonsilence_phones.txt' % data_dir
with open(psfn, 'w') as psf:
    for pws in sorted(ps):
        for p in sorted(list(ps[pws])):
            psf.write((u'%s ' % p).encode('utf8'))

        psf.write('\n')

logging.info ( '%s written.' % psfn )

psfn = '%s/local/dict.adapt/silence_phones.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\nSPN\nNSN\n')
logging.info ( '%s written.' % psfn )

psfn = '%s/local/dict.adapt/optional_silence.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\n')
logging.info ( '%s written.' % psfn )

psfn = '%s/local/dict.adapt/extra_questions.txt' % data_dir
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

logging.info ( '%s written.' % psfn )

logging.info ( "All done." )

