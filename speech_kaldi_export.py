#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2016 Guenter Bartsch
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
import utils
from speech_lexicon import ipa2xsampa, Lexicon
from speech_transcripts import Transcripts
from speech_tokenizer import tokenize
from speech_sequitur import sequitur_gen_ipa

WORKDIR = 'data/dst/speech/%s/kaldi'
LANG    = 'de'

#DEBUG_LIMIT = 5000
DEBUG_LIMIT = 0

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)

add_all = len(sys.argv)==2 and sys.argv[1] == '-a'

#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

#
# config
#

config = utils.load_config()

work_dir    = WORKDIR % LANG
kaldi_root  = config.get("speech", "kaldi_root")

data_dir    = "%s/data" % work_dir
mfcc_dir    = "%s/mfcc" % work_dir

wav16_dir   = config.get("speech", "wav16_dir_de")

#
# load lexicon, transcripts
#

print "loading lexicon..."
lex = Lexicon()
print "loading lexicon...done."

print "loading transcripts..."
transcripts = Transcripts()
ts_all, ts_train, ts_test = transcripts.split(limit=DEBUG_LIMIT, add_all=add_all)
print "loading transcripts (%d train, %d test) ...done." % (len(ts_train),
                                                            len(ts_test))
#
# create work_dir structure
#


utils.mkdirs('%s/lexicon' % data_dir)
utils.mkdirs('%s/local/dict' % data_dir)
utils.mkdirs(wav16_dir)
utils.mkdirs(mfcc_dir)

utils.symlink('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % work_dir)
utils.symlink('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % work_dir)

#
# kaldi data part
#

def export_kaldi_data (destdirfn, tsdict):

    global wav16_dir

    print "Exporting to %s..." % destdirfn

    utils.mkdirs(destdirfn)

    with open(destdirfn+'wav.scp','w') as wavscpf,  \
         open(destdirfn+'utt2spk','w') as utt2spkf, \
         open(destdirfn+'text','w') as textf:

        for utt_id in sorted(tsdict):
            ts = tsdict[utt_id]

            textf.write((u'%s %s\n' % (utt_id, ts['ts'])).encode('utf8'))

            wavscpf.write('%s %s/%s.wav\n' % (utt_id, wav16_dir, utt_id))

            utt2spkf.write('%s %s\n' % (utt_id, ts['spk']))

    utils.copy_file ('data/src/speech/%s/spk2gender' % LANG, '%s/spk2gender' % destdirfn)

export_kaldi_data('%s/train/' % data_dir, ts_train)
export_kaldi_data('%s/test/'  % data_dir, ts_test)


#
# add missing words to dictionary using sequitur, if add_all is set
#

if add_all:

    print "looking for missing words..."

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

        ipas = sequitur_gen_ipa (lex_base)

        print u"%5d/%5d Adding missing word : %s [ %s ]" % (cnt, len(missing), item[0], ipas)

        lex_entry = {'ipa': ipas}
        lex[lex_base] = lex_entry
        cnt += 1
        


#
# dictionary export
#

dictfn2 = '%s/local/dict/lexicon.txt' % data_dir

print "Exporting dictionary..." 

utt_dict = {}

for ts in ts_all:

    tsd = ts_all[ts]

    tokens = tsd['ts'].split(' ')

    # print repr(ts), repr(tokens)

    for token in tokens:
        if token in utt_dict:
            continue

        if not token in lex.dictionary:
            print "*** ERROR: missing token in dictionary: '%s' (tsd=%s, tokens=%s)" % (token, repr(tsd), repr(tokens))
            sys.exit(1)

        utt_dict[token] = lex.dictionary[token]['ipa']

ps = {}

with open (dictfn2, 'w') as dictf:

    dictf.write('!SIL SIL\n')

    # FIXME: re-enable once we have noise tokens in our transcripts
    # dictf.write('<SPOKEN_NOISE> SPN\n')
    dictf.write('<UNK> SPN\n')
    # dictf.write('<NOISE> NSN\n')

    for token in sorted(utt_dict):

        ipa = utt_dict[token]
        xsr = ipa2xsampa (token, ipa, spaces=True)

        xs = xsr.replace('-','').replace('\' ', '\'').replace('  ', ' ')

        dictf.write((u'%s %s\n' % (token, xs)).encode('utf8'))

        for p in xs.split(' '):

            if len(p)<1:
                print u"****ERROR: empty phoneme in : '%s' ('%s', ipa: '%s')" % (xs, xsr, ipa)

            pws = p[1:] if p[0] == '\'' else p

            if not pws in ps:
                ps[pws] = set([p])
            else:
                ps[pws].add(p)

print "%s written." % dictfn2

print "Exporting dictionary ... done."

#
# phoneme sets
#

# print "Phoneme set:", repr(ps)

psfn = '%s/local/dict/nonsilence_phones.txt' % data_dir
with open(psfn, 'w') as psf:
    for pws in ps:
        for p in sorted(list(ps[pws])):
            psf.write((u'%s ' % p).encode('utf8'))

        psf.write('\n')

print '%s written.' % psfn

psfn = '%s/local/dict/silence_phones.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\nSPN\nNSN\n')
print '%s written.' % psfn

psfn = '%s/local/dict/optional_silence.txt' % data_dir
with open(psfn, 'w') as psf:
    psf.write('SIL\n')
print '%s written.' % psfn

psfn = '%s/local/dict/extra_questions.txt' % data_dir
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

print '%s written.' % psfn

#
# language model
#

utils.mkdirs ('%s/local/lm' % data_dir)

fn = '%s/local/lm/train_nounk.txt' % data_dir

with open(fn, 'w') as f:
    
    for utt_id in sorted(transcripts):
        ts = transcripts[utt_id]
        f.write((u'%s\n' % ts['ts']).encode('utf8'))

print "%s written." % fn

fn = '%s/local/lm/wordlist.txt' % data_dir

with open(fn, 'w') as f:
    
    for token in sorted(utt_dict):
        f.write((u'%s\n' % token).encode('utf8'))

print "%s written." % fn

#
# copy scripts and config files
#

utils.copy_file ('data/src/speech/kaldi-run.sh', '%s/run.sh' % work_dir)
utils.copy_file ('data/src/speech/kaldi-run-nnet3.sh', '%s/run-nnet3.sh' % work_dir)
utils.copy_file ('data/src/speech/kaldi-cmd.sh', '%s/cmd.sh' % work_dir)
utils.copy_file ('data/src/speech/kaldi-path.sh', '%s/path.sh' % work_dir)
utils.mkdirs ('%s/conf' % work_dir)
utils.copy_file ('data/src/speech/kaldi-mfcc.conf', '%s/conf/mfcc.conf' % work_dir)
utils.copy_file ('data/src/speech/kaldi-mfcc-hires.conf', '%s/conf/mfcc_hires.conf' % work_dir)
utils.copy_file ('data/src/speech/kaldi-online-cmvn.conf', '%s/conf/online_cmvn.conf' % work_dir)
utils.mkdirs ('%s/local' % work_dir)
utils.copy_file ('data/src/speech/kaldi-build-lm.sh', '%s/local/build_lm.sh' % work_dir)
utils.copy_file ('data/src/speech/kaldi-score.sh', '%s/local/score.sh' % work_dir)

#
# main
#

print "All done."
print


