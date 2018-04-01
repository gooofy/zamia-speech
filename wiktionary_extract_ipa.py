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
# extract pronounciations from (german, for now) wiktionary
#

import os
import sys
import xml.sax
import re
import string
import codecs

from nltools                import misc

PROC_TITLE      = 'wiktionary_extract_ipa'
# ARTICLE_LIMIT = 1000
ARTICLE_LIMIT   = 0
DICTFN          = 'data/dst/speech/de/dict_wiktionary_de.txt'

# :{{IPA}} {{Lautschrift|çi}}
IPA_PATTERN = re.compile(r"^:{{IPA}} {{Lautschrift\|([^}]+)}}")

# :ver·rückt, {{Komp.}} ver·rück·ter, {{Sup.}} ver·rück·tes·ten
HYP_PATTERN = re.compile(r"^:([^,]+)")

article_cnt = 0
ipa_cnt     = 0

class ArticleExtractor(xml.sax.ContentHandler):

    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
 
    def startElement(self, name, attrs):
        #print("startElement '" + name + "'")
        self.ce = name

        if name == 'title':
            self.title = ''
        if name == 'text':
            self.text = ''


    def characters(self, content):

        if self.ce == 'title':
            self.title += content
        elif self.ce == 'text':
            self.text += content 

    def endElement(self, name):

        global article_cnt, ipa_cnt, dictf

        #print("endElement '" + name + "'")
        if name == 'page':

            article_cnt += 1

            title = self.title.lstrip().rstrip()
            body  = self.text.lstrip().rstrip()

            ipa         = None
            hyphenation = None
            hyp_armed   = False

            for line in body.split('\n'):
                if not ipa:
                    m = IPA_PATTERN.match(line)
                    if m:
                        ipa = m.group(1)
                if not hyphenation:
                    if hyp_armed:
                        hyp_armed = False
                        m = HYP_PATTERN.match(line)
                        if m:
                            hyphenation = m.group(1)
                    if u'{{Worttrennung}}' in line:
                        hyp_armed = True

            if not ipa:
                print "%7d %7d %s NO PRONOUNCIATION FOUND." % (article_cnt, ipa_cnt, title)
                return
            if not hyphenation:
                print "%7d %7d %s NO HYPHENTATION   FOUND." % (article_cnt, ipa_cnt, title)
                return

            ipa_cnt     += 1
            print u"%7d %7d %s IPA: %s" % (article_cnt, ipa_cnt, title, ipa)

            dictf.write('%s;%s\n' % (hyphenation, ipa))

            if ARTICLE_LIMIT and article_cnt >= ARTICLE_LIMIT:
                sys.exit(0)

#
# init
#

misc.init_app(PROC_TITLE)

#
# load config, set up global variables
#

config = misc.load_config ('.speechrc')

wikfn  = config.get("speech", "wiktionary_de")

#
# main program: SAX parsing of wiktionary dump
#

dictf = codecs.open(DICTFN, 'w', 'utf8')

source = open(wikfn)
xml.sax.parse(source, ArticleExtractor())

dictf.close()

print "%s written." % DICTFN

