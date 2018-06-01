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
# adapt an existing kaldi model to a dict and language model
#

import os
import sys
import logging
import readline
import atexit
import traceback

from optparse import OptionParser
from StringIO import StringIO

from nltools                import misc
from nltools.tokenizer      import tokenize
from nltools.phonetics      import ipa2xsampa

from speech_lexicon         import Lexicon
from speech_transcripts     import Transcripts

#
# init 
#

misc.init_app ('speech_kaldi_adapt')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] src_model_dir dict (lm.arpa|G.src.fst|grammar.jsgf) dst_model")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 4:
    parser.print_usage()
    sys.exit(1)

src_model = args[0]
dict_name = args[1]
lm_name   = args[2]
dst_model = args[3]

dst_dir   = 'data/dst/asr-models/kaldi/%s' % dst_model

#
# config
#

kaldi_root  = config.get("speech", "kaldi_root")

#
# load lexicon, transcripts
#

logging.info("loading lexicon...")
lex = Lexicon(file_name=dict_name)
logging.info("loading lexicon...done.")

#
# dictionary export
#

misc.mkdirs('%s/data/local/dict.adapt' % dst_dir)

dictfn2 = '%s/data/local/dict.adapt/lexicon.txt' % dst_dir

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

psfn = '%s/data/local/dict.adapt/nonsilence_phones.txt' % dst_dir
with open(psfn, 'w') as psf:
    for pws in sorted(ps):
        for p in sorted(list(ps[pws])):
            psf.write((u'%s ' % p).encode('utf8'))

        psf.write('\n')

logging.info ( '%s written.' % psfn )

psfn = '%s/data/local/dict.adapt/silence_phones.txt' % dst_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\nSPN\nNSN\n')
logging.info ( '%s written.' % psfn )

psfn = '%s/data/local/dict.adapt/optional_silence.txt' % dst_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\n')
logging.info ( '%s written.' % psfn )

psfn = '%s/data/local/dict.adapt/extra_questions.txt' % dst_dir
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

#
# language model / grammar
#

if lm_name.endswith('arpa'):
    misc.copy_file (lm_name, '%s/lm.arpa' % dst_dir)
else:
    misc.copy_file (lm_name, '%s/G.src.fst' % dst_dir)


#
# create skeleton dst model
#

misc.mkdirs ('%s/exp/%s'  % (dst_dir, dst_model))

misc.copy_file ('%s/model/final.mdl' % src_model, '%s/exp/%s/final.mdl' % (dst_dir, dst_model))
misc.copy_file ('%s/model/cmvn_opts' % src_model, '%s/exp/%s/cmvn_opts' % (dst_dir, dst_model))
misc.copy_file ('%s/model/tree'      % src_model, '%s/exp/%s/tree'      % (dst_dir, dst_model))

if os.path.exists('%s/extractor' % src_model):

    misc.mkdirs ('%s/exp/%s/extractor' % (dst_dir, dst_model))

    misc.copy_file ('%s/extractor/final.mat'         % src_model, '%s/exp/%s/extractor/final.mat'         % (dst_dir, dst_model))
    misc.copy_file ('%s/extractor/global_cmvn.stats' % src_model, '%s/exp/%s/extractor/global_cmvn.stats' % (dst_dir, dst_model))
    misc.copy_file ('%s/extractor/final.dubm'        % src_model, '%s/exp/%s/extractor/final.dubm'        % (dst_dir, dst_model))
    misc.copy_file ('%s/extractor/final.ie'          % src_model, '%s/exp/%s/extractor/final.ie'          % (dst_dir, dst_model))
    misc.copy_file ('%s/extractor/splice_opts'       % src_model, '%s/exp/%s/extractor/splice_opts'       % (dst_dir, dst_model))

    misc.mkdirs ('%s/exp/%s/ivectors_test_hires/conf' % (dst_dir, dst_model))

    misc.copy_file ('%s/extractor/splice.conf'       % src_model, '%s/exp/%s/ivectors_test_hires/conf'    % (dst_dir, dst_model))

#
# copy scripts and config files
#
 
misc.render_template('data/src/speech/kaldi-run-adaptation.sh.template', '%s/run-adaptation.sh' % dst_dir, dst_model=dst_model)
misc.copy_file ('data/src/speech/kaldi-cmd.sh', '%s/cmd.sh' % dst_dir)
misc.render_template('data/src/speech/kaldi-path.sh.template', '%s/path.sh' % dst_dir, kaldi_root=kaldi_root)
misc.symlink('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % dst_dir)
misc.symlink('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % dst_dir)


#
# main
#

logging.info ( "All done." )

