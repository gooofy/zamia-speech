#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017, 2018, 2019 Guenter Bartsch
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
# extract pronounciations from (english and german, for now) wiktionary
#

import os
import sys
import xml.sax
import re
import string
import codecs
import logging

from optparse           import OptionParser
from nltools            import misc
from functools          import reduce

PROC_TITLE      = 'wiktionary_extract_ipa'
# ARTICLE_LIMIT   = 100
ARTICLE_LIMIT   = 0
DICTFN          = 'data/dst/speech/%s/dict_wiktionary_%s.txt'
WORDLISTFN      = 'data/dst/speech/%s/wordlist_wiktionary_%s.txt'


IPA_PATTERN = {      # :{{IPA}} {{Lautschrift|çi}}
               'de': re.compile(r"^:{{IPA}} {{Lautschrift\|([^}]+)}}"),
                     # * {{IPA|/ˈkɑmədɔɹ/|lang=en}}
               'en': re.compile(r"{{IPA\|([^|]+)\|.*lang=en}}"),
              }

ALPHABET    = {'de': set(u"abcdefghijklmnopqrstuvwxyzäöüß"),
               'en': set(u"abcdefghijklmnopqrstuvwxyz'") }

# :ver·rückt, {{Komp.}} ver·rück·ter, {{Sup.}} ver·rück·tes·ten
HYP_PATTERN = re.compile(r"^:([^,]+)")

article_cnt = 0
ipa_cnt     = 0

class ArticleExtractor(xml.sax.ContentHandler):

    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
 
    def startElement(self, name, attrs):

        self.ce = name

        if name == 'title':
            self.title = ''
        if name == 'text':
            self.text = ''

        if name == 'page':
            loc = self._locator
            if loc is not None:
                line, col = loc.getLineNumber(), loc.getColumnNumber()
            else:
                line, col = 'unknown', 'unknown'
            logging.debug('page starts at line %s col %s' % (line, col))

    def characters(self, content):

        if self.ce == 'title':
            self.title += content
        elif self.ce == 'text':
            self.text += content 

    def endElement(self, name):

        global article_cnt, ipa_cnt, dictf, options, wordlistf

        #print("endElement '" + name + "'")
        if name == 'page':

            article_cnt += 1

            title = self.title.lstrip().rstrip()
            body  = self.text.lstrip().rstrip()

            ipa         = None
            hyphenation = None
            hyp_armed   = False
            german      = False

            for line in body.split('\n'):
                if not ipa:
                    for m in IPA_PATTERN[options.lang].findall(line):
                        ipa = m
                        break # pick the first one
                if not hyphenation:
                    if hyp_armed:
                        hyp_armed = False
                        m = HYP_PATTERN.match(line)
                        if m:
                            hyphenation = m.group(1)
                    if u'{{Worttrennung}}' in line:
                        hyp_armed = True
                if not german:
                    if u'{{Sprache|Deutsch}}' in line:
                        german = True

            if options.lang == 'de':
                if not german:
                    logging.debug("%7d %7d %s NOT GERMAN." % (article_cnt, ipa_cnt, title))
                    return
                # all characters used in title covered by our alphabet?
                alphacheck = reduce(lambda t, c: False if not t else c.lower() in ALPHABET[options.lang], title, True)
                if not alphacheck:
                    logging.debug("%7d %7d %s NOT COVERED BY ALPHABET." % (article_cnt, ipa_cnt, repr(title)))
                    return
                wordlistf.write('%s\n' % title)
                if not ipa:
                    logging.debug("%7d %7d %s NO PRONOUNCIATION FOUND." % (article_cnt, ipa_cnt, title))
                    return
                if not hyphenation:
                    logging.debug("%7d %7d %s NO HYPHENTATION   FOUND." % (article_cnt, ipa_cnt, title))
                    return
            elif options.lang == 'en':
                # all characters used in title covered by our alphabet?
                alphacheck = reduce(lambda t, c: False if not t else c.lower() in ALPHABET[options.lang], title, True)
                if not alphacheck:
                    logging.debug("%7d %7d %s NOT COVERED BY ALPHABET." % (article_cnt, ipa_cnt, repr(title)))
                    return

                wordlistf.write('%s\n' % title)

                if not ipa:
                    logging.debug("%7d %7d %s NO PRONOUNCIATION FOUND." % (article_cnt, ipa_cnt, title))
                    return

                hyphenation = title

            ipa_cnt     += 1
            logging.info(u"%7d %7d %s IPA: %s" % (article_cnt, ipa_cnt, title, ipa))

            dictf.write('%s;%s\n' % (hyphenation, ipa))

            if ARTICLE_LIMIT and article_cnt >= ARTICLE_LIMIT:
                logging.warn('DEBUG limit of %d reached -> exit.' % ARTICLE_LIMIT)
                sys.exit(0)

#
# init
#

misc.init_app(PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %%prog [options]")

parser.add_option ("-l", "--lang", dest="lang", type = "str", default="de",
                   help="language (default: de)")

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

for c in ALPHABET[options.lang]:
    logging.debug(c)

#
# load config, set up global variables
#

config = misc.load_config ('.speechrc')

wikfn  = config.get("speech", "wiktionary_%s" % options.lang)


#
# main program: SAX parsing of wiktionary dump
#

dictf     = codecs.open(DICTFN % (options.lang, options.lang), 'w', 'utf8')
wordlistf = codecs.open(WORDLISTFN % (options.lang, options.lang), 'w', 'utf8')

source = codecs.open(wikfn, 'r', 'utf8')
xml.sax.parse(source, ArticleExtractor())

dictf.close()
wordlistf.close()

logging.info("%s written." % (DICTFN % (options.lang, options.lang)))
logging.info("%s written." % (WORDLISTFN % (options.lang, options.lang)))

