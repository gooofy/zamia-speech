#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016 Guenter Bartsch
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
# generate training sentences for language models
#
# - train NLTK's punkt sentence segmenter on german parole corpus
# - use it to extract sentences from parole corpus
# - add sentences from europarl
#

import sys
import re
import os
import traceback
import nltk
import pickle
from os.path import expanduser
import StringIO
import ConfigParser
import codecs

from utils import compress_ws

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

from speech_tokenizer import tokenize

DEBUG_SGM_LIMIT = 0
PUNKT_PICKLEFN  = 'data/dst/speech/de/punkt.pickle'
SENTENCEFN      = 'data/dst/speech/de/sentences.txt'

ENABLE_TRAINING = True

class ParoleParser(HTMLParser):

    def __init__  (self, processfn):

        HTMLParser.__init__  (self)

        self.in_par    = False
        self.processfn = processfn

    def handle_starttag(self, tag, attrs):
        #print "Encountered a start tag:", tag
        if tag == 'p':
            self.in_par = True
            self.buf = u""

    def handle_endtag(self, tag):
    
        global sentf, sentcnt, rawcnt, sentences

        if tag == 'p':
            self.in_par = False
            #print (u"PAR: %s" % self.buf).encode('UTF8')

            text = compress_ws(self.buf.replace('\n', ' '))

            self.processfn(text)

    def handle_data(self, data):
        if self.in_par and len(data)>0:
            #print "About to add: %s" % repr(data)
            self.buf += data.decode('UTF8', 'ignore')

    def handle_entityref (self, name):
        if self.in_par:
            c = ''
            if name == 'star':
                c = u'*'
            elif name == 'bquot':
                c = u'"'
            elif name == 'equot':
                c = u'"'
            elif name == 'lowbar':
                c = u'_'
            elif name == 'parole.tax':
                c = u''
            else:
                if name in name2codepoint:
                    c = unichr(name2codepoint[name])
                else: 
                    print "unknown entityref: %s" % name
                    c = ''
            #print "Named ent:", c
            self.buf += c

def parole_crawl (path, processfn):

    num_files = 0

    files = os.listdir (path)
    for file in files:

        if DEBUG_SGM_LIMIT>0 and num_files > DEBUG_SGM_LIMIT:
            return num_files

        p = "%s/%s" % (path, file)

        if os.path.isdir(p):
            num_files += parole_crawl(p, processfn)
            continue
        
        if not p.endswith ('.sgm'):
            continue

        print "%3d: found sgm: %s" % (num_files, p)
        num_files += 1

        pp = ParoleParser(processfn)

        with codecs.open(p, 'r', 'utf8', 'ignore') as inf:
            while True:
                sgmldata = inf.read(1024)
                if not sgmldata:
                    break
                pp.feed(sgmldata)

        pp.close()

    return num_files

def train_punkt (text):

    global punkt_trainer, punkt_count

    punkt_count += 1

    if punkt_count % 1000 == 0:
        print "%5d train_punkt: %s" % (punkt_count, text[:80])

    punkt_trainer.train(text, finalize=False, verbose=False)

def apply_punkt (text):

    global tokenizer, outf

    sentncs = tokenizer.tokenize(text, realign_boundaries=True)
    for sentence in sentncs:

        print "Sentence: %s" % sentence

        outf.write(u'%s\n' % ' '.join(tokenize(sentence)))

#
# init terminal
#

reload(sys)
sys.setdefaultencoding('utf-8')
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

#
# load config, set up global variables
#

home_path = expanduser("~")

config = ConfigParser.RawConfigParser()
config.read("%s/%s" % (home_path, ".nlprc"))

parole    = config.get("speech", "parole_de")
europarl  = config.get("speech", "europarl_de")

if ENABLE_TRAINING:
    #
    # punkt tokenizer training
    #

    print "training punkt..."

    punkt_trainer = nltk.tokenize.punkt.PunktTrainer()

    punkt_count = 0

    parole_crawl (parole, train_punkt)

    print
    print "Finalizing training..."
    punkt_trainer.finalize_training(verbose=True)
    print "Training done. %d text segments." % punkt_count
    print

    params = punkt_trainer.get_params()
    # print "Params: %s" % repr(params)

    tokenizer = nltk.tokenize.punkt.PunktSentenceTokenizer(params)
    with open(PUNKT_PICKLEFN, mode='wb') as f:
            pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)

    print '%s written.' % PUNKT_PICKLEFN

else:

    print "Loading %s ..." % PUNKT_PICKLEFN

    with open(PUNKT_PICKLEFN, mode='rb') as f:
        tokenizer = pickle.load(f)

    print "Loading %s ... done." % PUNKT_PICKLEFN

with codecs.open(SENTENCEFN, 'w', 'utf8') as outf:

    print "applying punkt to parole..."
    parole_crawl (parole, apply_punkt)

    print "adding sentences from europarl..."
    with codecs.open(europarl, 'r', 'utf8') as inf:
        for line in inf:
            outf.write(u'%s\n' % ' '.join(tokenize(line)))

print '%s written.' % SENTENCEFN
print 

