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
# extract wkt (word replacement table) entries from german wiktionary
#

import os
import sys
import xml.sax
import re
import string
import codecs

from nltools                import misc

PROC_TITLE      = 'wiktionary_extract_ipa'
# ARTICLE_LIMIT = 10000
ARTICLE_LIMIT   = 0
WRTFN           = 'data/src/wrt/wiktionary.csv'

# {{Alte Schreibweise|Kirchturm|Reform 1901}}
WRT_PATTERN = re.compile(r"^\{\{Alte Schreibweise\|([^}|]+)")

article_cnt = 0
wrt_cnt     = 0

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

        global article_cnt, wrt_cnt, dictf

        #print("endElement '" + name + "'")
        if name == 'page':

            article_cnt += 1

            title = self.title.lstrip().rstrip().lower()
            body  = self.text.lstrip().rstrip()

            wrt         = None
            german      = False

            for line in body.split('\n'):
                if not wrt:
                    m = WRT_PATTERN.match(line)
                    if m:
                        wrt = m.group(1).lower()
                        # print 'matched: %s -> %s' % (line, wrt)
                if not german:
                    if u'{{Sprache|Deutsch}}' in line:
                        german = True

            if not german:
                print "%7d %7d %s NOT GERMAN." % (article_cnt, wrt_cnt, title)
                return
            if not wrt:
                print "%7d %7d %s NO WRT ENTRY FOUND." % (article_cnt, wrt_cnt, title)
                return
            if u' ' in wrt or u' ' in title:
                print "%7d %7d %s SPACE." % (article_cnt, wrt_cnt, title)
                return

            wrt_cnt     += 1
            print u"%7d %7d %s WRT: %s" % (article_cnt, wrt_cnt, title, wrt)

            wrtf.write(u"        %-20s: u'%s',\n" % ("u'"+title+"'", wrt))

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

wrtf = codecs.open(WRTFN, 'w', 'utf8')

source = open(wikfn)
xml.sax.parse(source, ArticleExtractor())

wrtf.close()

print "%s written." % WRTFN

