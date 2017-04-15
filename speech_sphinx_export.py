#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017 Guenter Bartsch
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
# export speech training data to create a CMU Sphinx training cases
#

import sys
import re
import os
from os.path import expanduser
import StringIO
import ConfigParser
from optparse import OptionParser
import logging
import codecs

from nltools import misc

from nltools.phonetics  import ipa2xsampa, xsampa2ipa, xsampa2xarpabet
from speech_lexicon     import Lexicon
from speech_transcripts import Transcripts

WORKDIR_CONT = 'data/dst/speech/%s/cmusphinx_cont'
WORKDIR_PTM  = 'data/dst/speech/%s/cmusphinx_ptm'

NJOBS = 8

#
# init 
#

misc.init_app ('speech_sphinx_export')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-d", "--debug", dest="debug", type='int', default=0,
                   help="limit number of transcripts (debug purposes only), default: 0 (unlimited)")
parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")
parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

wav16_dir   = config.get("speech", "wav16_dir_%s" % options.lang)

#
# load lexicon, transcripts
#

logging.info("loading lexicon...")
lex = Lexicon()
logging.info("loading lexicon...done.")

logging.info("loading transcripts...")
transcripts = Transcripts()
ts_all, ts_train, ts_test = transcripts.split(limit=options.debug)
logging.info("loading transcripts (%d train, %d test) ...done." % (len(ts_train), len(ts_test)))

def export_sphinx_case(work_dir, sphinxtrain_cfg_fn):

    #
    # language model
    #

    misc.mkdirs('%s' % work_dir)

    fn = '%s/prompts.sent' % work_dir

    with codecs.open(fn, 'w', 'utf8') as outf:

        for cfn in ts_all:

            transcript = transcripts[cfn]['ts']

            outf.write ('%s\n' % transcript)

    logging.info("%s written." % fn)

    fn = '%s/wlist.txt' % work_dir

    with codecs.open(fn, 'w', 'utf8') as outf:

        for word in lex:

            outf.write ('%s\n' % word)

    logging.info( "%s written." % fn)

    #
    # create work_dir structure
    #

    mfcc_dir    = "%s/mfcc" % work_dir

    misc.mkdirs('%s/logs' % work_dir)
    misc.mkdirs('%s/etc'  % work_dir)
    misc.mkdirs('%s' % mfcc_dir)

    # generate sphinx_train.cfg, featdir in there

    # inf = codecs.open ('data/src/speech/sphinx_train.cfg', 'r', 'utf8')
    # outf = codecs.open ('%s/etc/sphinx_train.cfg' % work_dir, 'w', 'utf8')
    # for line in inf:
    #     s = line.replace('%FEATDIR%', mfcc_dir).replace('%WORKDIR%', work_dir)
    #     outf.write (s)
    # inf.close()
    # outf.close()

    misc.copy_file (sphinxtrain_cfg_fn, '%s/etc/sphinx_train.cfg' % work_dir)
    misc.copy_file ('data/src/speech/sphinx-voxforge.filler', '%s/etc/voxforge.filler' % work_dir)
    misc.copy_file ('data/src/speech/sphinx-feat.params', '%s/etc/feat.params' % work_dir)

    # generate dict

    phoneset = set()

    pdfn = '%s/etc/voxforge.dic' % work_dir
    with codecs.open (pdfn, 'w', 'utf8') as pdf:

        for word in lex:

            ipa = lex[word]['ipa']

            xs  = ipa2xsampa(word, ipa)
            xa  = xsampa2xarpabet(word, xs)

            pdf.write (u'%s %s\n' % (word, xa))

            phones = xa.split(' ')
            for phone in phones:

                if len(phone.strip()) == 0:
                    logging.error(u"***ERROR: empty phone detected in lex entry %s %s" % (word, ipa))

                phoneset.add(phone)
        
    logging.info("%s written." % pdfn)

    logging.info("Got %d phones." % len(phoneset))

    phfn = '%s/etc/voxforge.phone' % work_dir
    with codecs.open (phfn, 'w', 'utf8') as phf:

        for phone in phoneset:
            phf.write (u'%s\n' % phone)

        phf.write (u'SIL\n')

    logging.info("%s written." % phfn)

    #
    # prompts
    #

    train_fifn = '%s/etc/voxforge_train.fileids'       % work_dir
    train_tsfn = '%s/etc/voxforge_train.transcription' % work_dir
    test_fifn  = '%s/etc/voxforge_test.fileids'        % work_dir
    test_tsfn  = '%s/etc/voxforge_test.transcription'  % work_dir
    runfeatfn  = '%s/run-feat.sh'                      % work_dir

    SPHINXFE = "sphinx_fe -i '%s' -part 1 -npart 1 -ei wav -o '%s' -eo mfc -nist no -raw no -mswav yes -samprate 16000 -lowerf 130 -upperf 6800 -nfilt 25 -transform dct -lifter 22 >>logs/mfcc%02d.log 2>&1 &\n"
    with codecs.open (runfeatfn,  'w', 'utf8') as runfeatf:

        runfeatf.write('#!/bin/bash\n\n')

        cnt = 0
        for cfn in ts_all:

            w16filename = "%s/%s.wav" % (wav16_dir, cfn)
            mfcfilename = "mfcc/%s.mfc" % cfn
            runfeatf.write(SPHINXFE % (w16filename, mfcfilename, cnt) )
            cnt = (cnt + 1) % NJOBS

            if cnt == 0:
                runfeatf.write('wait\n')

    logging.info("%s written." % runfeatfn)

    with codecs.open (train_fifn, 'w', 'utf8') as train_fif, \
         codecs.open (train_tsfn, 'w', 'utf8') as train_tsf, \
         codecs.open (test_fifn,  'w', 'utf8') as test_fif,  \
         codecs.open (test_tsfn,  'w', 'utf8') as test_tsf:

        for cfn in ts_train:
            train_fif.write ('%s\n' % cfn)
            train_tsf.write (u'<s> %s </s> (%s)\n' % (ts_train[cfn]['ts'], cfn))

        for cfn in ts_test:
            test_fif.write ('%s\n' % cfn)
            test_tsf.write (u'<s> %s </s> (%s)\n' % (ts_test[cfn]['ts'], cfn))

    logging.info ("%s written." % train_tsfn)
    logging.info ("%s written." % train_fifn)
    logging.info ("%s written." % test_tsfn)
    logging.info ("%s written." % test_fifn)

    misc.copy_file ('data/src/speech/sphinx-run.sh', '%s/sphinx-run.sh' % work_dir)

# we create two different training cases in separate subdirs here, one for a continous and one for a ptm model

export_sphinx_case(WORKDIR_CONT % options.lang, 'data/src/speech/sphinx_train_cont.cfg')
export_sphinx_case(WORKDIR_PTM  % options.lang, 'data/src/speech/sphinx_train_ptm.cfg')

