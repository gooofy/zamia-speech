#
# Copyright 2018 Marc Puels
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
# Parser and Punkt Tokenizer working on the German Parole Corpus
#

import codecs
import logging
import pickle
import os

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

from nltools.misc import compress_ws
from nltools.tokenizer import tokenize

from pathlib2 import Path

SENTENCES_STATS = 1000
PUNKT_PICKLEFN  = Path('data/dst/tokenizers/punkt-de.pickle')

class ParoleParser(HTMLParser):

    def __init__(self, processfn):

        HTMLParser.__init__(self)

        self.in_par = False
        self.processfn = processfn

    def handle_starttag(self, tag, attrs):
        # print "Encountered a start tag:", tag
        if tag == 'p':
            self.in_par = True
            self.buf = u""

    def handle_endtag(self, tag):

        global sentf, sentcnt, rawcnt, sentences

        if tag == 'p':
            self.in_par = False
            # print (u"PAR: %s" % self.buf).encode('UTF8')

            text = compress_ws(self.buf.replace('\n', ' '))

            self.processfn(text)

    def handle_data(self, data):
        if self.in_par and len(data) > 0:
            # print "About to add: %s" % repr(data)
            self.buf += data.decode('UTF8', 'ignore')

    def handle_entityref(self, name):
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
                    logging.warning("unknown entityref: %s" % name)
                    c = ''
            # print "Named ent:", c
            self.buf += c


def parole_crawl(path, processfn, debug_sgm_limit):
    num_files = 0

    files = os.listdir(path)
    for file in files:
        if debug_sgm_limit > 0 and num_files > debug_sgm_limit:
            return num_files

        p = "%s/%s" % (path, file)

        if os.path.isdir(p):
            num_files += parole_crawl(p, processfn, debug_sgm_limit)
            continue

        if not p.endswith('.sgm'):
            continue

        logging.info("%8d: found sgm: %s" % (num_files, p))
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


class TrainPunktWrapper:
    def __init__(self, punkt_trainer):
        self._punkt_trainer = punkt_trainer
        self.punkt_count = 0

    def train_punkt(self, text):
        self.punkt_count += 1
        if self.punkt_count % 1000 == 0:
            logging.info("%8d train_punkt: %s" % (self.punkt_count, text[:80]))

        self._punkt_trainer.train(text, finalize=False, verbose=False)


class ApplyPunktWrapper:
    def __init__(self, tokenizer, outf):
        self._tokenizer = tokenizer
        self._outf = outf
        self._num_sentences = 0

    def apply_punkt(self, text):
        sentncs = self._tokenizer.tokenize(text, realign_boundaries=True)
        for sentence in sentncs:

            logging.debug("sentence: %s" % sentence)
            self._outf.write(u'%s\n' % ' '.join(tokenize(sentence)))

            self._num_sentences += 1
            if self._num_sentences % SENTENCES_STATS == 0:
                logging.info('%8d sentences.' % self._num_sentences)


def load_punkt_tokenizer():
    try:
        with open(str(PUNKT_PICKLEFN), mode='rb') as f:
            return pickle.load(f)
    except IOError as e:
        print(
            "Could not find pickled Punkt tokenizer in {}. Please train it "
            "first by executing `speech_train_punkt_tokenizer.py`.".format(
                PUNKT_PICKLEFN))
        print
        raise e
