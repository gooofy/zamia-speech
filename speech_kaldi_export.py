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
# export speech training data to create a kaldi case
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
from nltools.sequiturclient import sequitur_gen_ipa

from speech_lexicon     import Lexicon
from speech_transcripts import Transcripts

WORKDIR          = 'data/dst/speech/%s/kaldi'
SEQUITUR_MODEL   = 'data/models/sequitur-voxforge-%s-latest'

#
# init 
#

misc.init_app ('speech_kaldi_export')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-a", "--add-all", action="store_true", dest="add_all",
                   help="use all transcripts, generate missing words using sequitur g2p")
parser.add_option ("-d", "--debug", dest="debug", type='int', default=0,
                   help="limit number of transcripts (debug purposes only), default: 0 (unlimited)")
parser.add_option ("-l", "--lang", dest="lang", type = "str", default='de',
                   help="language (default: de)")
parser.add_option ("-p", "--prompt-words", action="store_true", dest="prompt_words",
                   help="limit dict to tokens covered in prompts")
parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

work_dir    = WORKDIR %options.lang 
kaldi_root  = config.get("speech", "kaldi_root")

data_dir    = "%s/data" % work_dir
mfcc_dir    = "%s/mfcc" % work_dir

wav16_dir   = config.get("speech", "wav16_dir_%s" % options.lang)

#
# load lexicon, transcripts
#

logging.info ( "loading lexicon...")
lex = Lexicon(lang=options.lang)
logging.info ( "loading lexicon...done.")

logging.info ( "loading transcripts...")
transcripts = Transcripts(lang=options.lang)
ts_all, ts_train, ts_test = transcripts.split(limit=options.debug, add_all=options.add_all)
logging.info ( "loading transcripts (%d train, %d test) ...done." % (len(ts_train), len(ts_test)))

#
# create work_dir structure
#


# FIXME: unused, remove misc.mkdirs('%s/lexicon' % data_dir)
misc.mkdirs('%s/local/dict' % data_dir)
misc.mkdirs(wav16_dir)
misc.mkdirs(mfcc_dir)

misc.symlink('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % work_dir)
misc.symlink('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % work_dir)

#
# kaldi data part
#

def export_kaldi_data (destdirfn, tsdict):

    global wav16_dir

    logging.info ( "Exporting to %s..." % destdirfn)

    misc.mkdirs(destdirfn)

    with open(destdirfn+'wav.scp','w') as wavscpf,  \
         open(destdirfn+'utt2spk','w') as utt2spkf, \
         open(destdirfn+'text','w') as textf:

        for utt_id in sorted(tsdict):
            ts = tsdict[utt_id]

            textf.write((u'%s %s\n' % (utt_id, ts['ts'])).encode('utf8'))

            wavscpf.write('%s %s/%s.wav\n' % (utt_id, wav16_dir, utt_id))

            utt2spkf.write('%s %s\n' % (utt_id, ts['spk']))

    misc.copy_file ('data/src/speech/%s/spk2gender' % options.lang, '%s/spk2gender' % destdirfn)

export_kaldi_data('%s/train/' % data_dir, ts_train)
export_kaldi_data('%s/test/'  % data_dir, ts_test)


#
# add missing words to dictionary using sequitur, if add_all is set
#

if options.add_all:

    logging.info ( "looking for missing words..." )

    missing = {} # word -> count

    num = len(transcripts)
    cnt = 0

    for cfn in transcripts:
        ts = transcripts[cfn]

        cnt += 1

        if ts['quality']>0:
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

        ipas = sequitur_gen_ipa (SEQUITUR_MODEL % options.lang, lex_base)

        logging.info ( u"%5d/%5d Adding missing word : %s [ %s ]" % (cnt, len(missing), item[0], ipas) )

        lex_entry = {'ipa': ipas}
        lex[lex_base] = lex_entry
        cnt += 1
        


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

