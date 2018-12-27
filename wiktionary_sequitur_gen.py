#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2018 Guenter Bartsch
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
# use the pre-trained wiktionary sequitur model to generate candidate lex entries, 
# validate them against our regular sequitur model, add ones that match to our lex 
#

import os
import sys
import string
import codecs
import logging
import traceback

from optparse               import OptionParser

from nltools                import misc
from speech_lexicon         import Lexicon
from nltools.sequiturclient import sequitur_gen_ipa, sequitur_gen_ipa_multi
from nltools.phonetics      import xsampa2ipa


PROC_TITLE       = 'wiktionary_sequitur_gen'
DICTFN           = 'data/dst/speech/de/dict_wiktionary_de.txt'
OUTDICTFN        = 'data/dst/speech/de/dict_wiktionary_gen.txt'
OUTREJFN         = 'data/dst/speech/de/dict_wiktionary_rej.txt'
CHUNKINRFN       = 'data/dst/speech/de/dict_wiktionary_chinr_%04d.txt'
CHUNKINWFN       = 'data/dst/speech/de/dict_wiktionary_chinw_%04d.txt'
CHUNKOUTRFN      = 'data/dst/speech/de/dict_wiktionary_choutr_%04d.txt'
CHUNKOUTWFN      = 'data/dst/speech/de/dict_wiktionary_choutw_%04d.txt'
SCRIPTFN         = 'data/dst/speech/de/dict_wiktionary_run_parallel.sh'
REGULAR_MODEL    = 'data/models/sequitur-dict-de.ipa-latest'
WIKTIONARY_MODEL = 'data/dst/speech/de/wiktionary_sequitur/model-6'
TEST_TOKEN       = u'aalbestand'

# CHUNK_SIZE       = 1000
CHUNK_SIZE       = 256
DEFAULT_NUM_CPUS = 4
# DEBUG_CHUNK_LIMIT= 12
DEBUG_CHUNK_LIMIT= 0

ALPHABET         = set([ u'a', u'b', u'c', u'd', u'e', u'f', u'g', u'h', u'i', u'j', u'k', u'l', u'm', u'n', u'o', u'p', u'q', u'r', u's', u't', u'u', u'v', u'w', u'x', u'y', u'z', u'ü', u'ö', u'ä', u'ß'])

#
# init
#

misc.init_app(PROC_TITLE)

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] )")

parser.add_option ("-n", "--num-cpus", dest="num_cpus", type="int", default=DEFAULT_NUM_CPUS,
                   help="number of cpus to use in parallel, default: %d" % DEFAULT_NUM_CPUS)

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# load config, set up global variables
#

config = misc.load_config ('.speechrc')

wikfn  = config.get("speech", "wiktionary_de")

                    # IPA_R  IPA_W
TOLERATABLE_DIFFS = [ (u'p', u'b'),
                      (u'b', u'p'),
                      (u'ɛ', u'ə'),
                      (u'ə', u'ɛ'),
                      (u'e', u'ɛ'),
                      (u'ɛ', u'e'),
                      (u'r', u'ʁ'),
                      (u'ʁ', u'r'),
                      (u'ɐ', u'ʁ'),
                      (u'ʁ', u'ɐ'),
                      (u'd', u't'),
                      (u't', u'd'),
                      (u'z', u's'),
                      (u's', u'z'),
                      (u'ʊ', u'u'),
                      (u'u', u'ʊ'),
                    ]

def merge_check(token, ipa_r, ipa_w):

    """ merge ipa_r and ipa_w into a "best-of" ipa_m:
        - take hyphenation from ipa_r since wiktionary does not have hyphens 
        - take stress from ipa_w unless there is no stress marker in ipa_w, then use ipa_r 
        - tolerate vocal length differences
        - tolerate differences listed above """
    
    ir = 0
    iw = 0

    ipa_m = u""

    stress_w = u"'" in ipa_w

    while (ir < len(ipa_r)) and (iw < len(ipa_w)):

        # print ir, iw, ipa_m

        if ipa_r[ir] == u"'":
            ir += 1 
            if not stress_w:
                 ipa_m += u"'"
            continue

        if ipa_r[ir] == u"ː" and ipa_w[iw] != u"ː":
            ir += 1
            continue
        if ipa_r[ir] != u"ː" and ipa_w[iw] == u"ː":
            iw += 1
            ipa_m += u"ː"
            continue

        if ipa_r[ir] == u"ʔ" and ipa_w[iw] != u"ʔ":
            ir += 1
            continue
        if ipa_r[ir] != u"ʔ" and ipa_w[iw] == u"ʔ":
            iw += 1
            ipa_m += u"ʔ"
            continue

        if ipa_r[ir] == u"-":
            ir += 1 
            ipa_m += u"-"
            continue

        if ipa_w[iw] == u"'":
            iw += 1 
            if stress_w:
                 ipa_m += u"'"
            continue
            
        if ipa_w[iw] != ipa_r[ir]:
            tolerate = False
            for tr, tw in TOLERATABLE_DIFFS:
                if (ipa_r[ir] == tr) and (ipa_w[iw] == tw):
                    tolerate = True
                    break
            if not tolerate:
                break
           
        ipa_m += ipa_w[iw]

        ir += 1
        iw += 1

    if ir==len(ipa_r) and iw==len(ipa_w):

        if token == TEST_TOKEN:
            print token
            print ipa_r
            print ipa_w
            print ipa_m

        return ipa_m
    return None 


# token = u"abakteriell"
# ipa_r = u"'ʔaːb-ak-'teː-ʁiː-'ɛl"
# ipa_w = u"ʔabakteːʁiː'ɛl"
# print merge_check(token, ipa_r, ipa_w)
# sys.exit(0)


#
# load lexicon
#

logging.info("loading lexicon...")
lex = Lexicon('dict-de.ipa')
logging.info("loading lexicon...done.")

#
# load wiktionary
#

logging.info("loading wiktionary...")
wiktionary = {}
wiktionary_reverse = {}
with codecs.open(DICTFN, 'r', 'utf8') as dictf:
    for line in dictf:
        parts = line.strip().split(';')
        if len(parts) != 2:
            # print "Failed to parse line %s" % line.strip()
            continue

        word  = parts[0]
        ipa   = parts[1].strip()

        if u" " in word:
            continue
        if u"''" in word:
            continue

        token = u''
        for c in word.lower():
            if c in ALPHABET:
                token += c

        if token in lex:
            logging.debug("%05d ignoring %s as it is already in our dict." % (len(wiktionary), token))
            continue

        wiktionary[token] = (word, ipa)
        wiktionary_reverse[ipa] = token

logging.info("loading wiktionary... done. %d entries." % len(wiktionary))

#
# predict missing entries
#

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

logging.info ('predicting missing entries in parallel...')

num_chunks = 0

with open(SCRIPTFN, 'w') as scriptf:

    for i, chunk in enumerate(chunks(sorted(wiktionary), CHUNK_SIZE)):

        with codecs.open(CHUNKINRFN % i, 'w', 'utf8') as chunkinrf:
            with codecs.open(CHUNKINWFN % i, 'w', 'utf8') as chunkinwf:

                for token in chunk:
                    w, ipa = wiktionary[token]

                    chunkinrf.write('%s\n' % token)
                    chunkinwf.write('%s\n' % ipa)

        scriptf.write('echo %04d\n' % i)
        scriptf.write('g2p.py -e utf-8 --model %s --apply %s > %s &\n' % (REGULAR_MODEL, CHUNKINRFN % i, CHUNKOUTRFN % i))
        scriptf.write('g2p.py --model %s --apply %s > %s &\n' % (WIKTIONARY_MODEL, CHUNKINWFN % i, CHUNKOUTWFN % i))
        num_chunks += 1
        if DEBUG_CHUNK_LIMIT and num_chunks > DEBUG_CHUNK_LIMIT:
            logging.warn('debug limit reached.')
            break

        if i % options.num_cpus == (options.num_cpus-1):
            scriptf.write('wait\n')

    scriptf.write('wait\n')

logging.info ('%s written.' % SCRIPTFN)
os.system('chmod 700 %s' % SCRIPTFN)
os.system(SCRIPTFN)

ipa_r_map = {}
ipa_w_map = {}

for chunkidx in range(num_chunks):

    with codecs.open(CHUNKOUTRFN % chunkidx, 'r', 'utf8') as chunkf:

        for line in chunkf:

            parts = line.strip().split('\t')

            if len(parts) < 2:
                continue

            try:
                word = parts[0]
                if word in wiktionary:

                    xs = parts[1]

                    ipa = xsampa2ipa(word, xs)
                    ipa_r_map[word] = ipa
            except:
                logging.error("Error processing line %s:" % line)
                logging.error(traceback.format_exc())

    with codecs.open(CHUNKOUTWFN % chunkidx, 'r', 'utf8') as chunkf:

        for line in chunkf:

            parts = line.strip().split('\t')

            if len(parts) < 2:
                continue

            try:
                ipan = parts[0]
                if ipan in wiktionary_reverse:

                    word = wiktionary_reverse[ipan]

                    xs = parts[1]

                    ipa = xsampa2ipa(word, xs)
                    ipa_w_map[word] = ipa
            except:
                logging.error("Error processing line %s:" % line)
                logging.error(traceback.format_exc())

# print repr(ipa_r_map)
# print repr(ipa_w_map)

with codecs.open(OUTDICTFN, 'w', 'utf8') as outdictf, \
     codecs.open(OUTREJFN, 'w', 'utf8')  as outrejf:

    cnt_matched = 0

    cnt = 0

    for token in ipa_r_map:

        if not token in ipa_w_map:
            continue

        try:

            ipa_r = ipa_r_map[token]
            ipa_w = ipa_w_map[token]

            # matched = ipa_r.replace(u"-", u"") == ipa_w
            ipa_m = merge_check(token, ipa_r, ipa_w)
            if ipa_m and (not u"'" in ipa_m): # at least one stress marker is required
                ipa_m = None

            # if matched:
            if ipa_m:
                logging.info("%6d/%6d %6d %-30s: %s vs %s MATCHED!" % (cnt, len(wiktionary), cnt_matched, token, ipa_r, ipa_w))
                cnt_matched += 1

                outdictf.write(u"%s;%s\n" % (token, ipa_m))

            else:
                logging.info("%6d/%6d %6d %-30s: %s vs %s" % (cnt, len(wiktionary), cnt_matched, token, ipa_r, ipa_w))
                outrejf.write(u"\n%s\nIPA_R %s\nIPA_W %s\n" % (token, ipa_r.replace(u"-", u""), ipa_w))
        except:
            logging.error(traceback.format_exc())

logging.info (" %s written." % OUTDICTFN)
logging.info (" %s written." % OUTREJFN)

