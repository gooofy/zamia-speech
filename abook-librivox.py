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
# retrieve audiobooks from librivox
#

import os
import sys
import logging
import traceback
import codecs
import urllib2
import json

from optparse import OptionParser

from nltools                import misc

ZIPDIR        = 'abook/incoming'
DBFN          = 'data/dst/speech/de/librivox.json'
# LIMIT         = 500
LIMIT         = 50

#
# init 
#

misc.init_app ('abook-librivox')

config = misc.load_config ('.speechrc')

#
# commandline parsing
#

parser = OptionParser("usage: %prog [options] dstdir [id]")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) < 1:
    parser.print_usage()
    sys.exit(1)

dstdirfn = args[0]

#
# fetch or load whole DB
#

books = []

if not os.path.exists(DBFN):

    offset = 0

    try:
        while True:

            print "offset:", offset, "books:", len(books)

            titles_json = urllib2.urlopen("https://librivox.org/api/feed/audiobooks/?format=json&limit=%d&offset=%d&extended=1" % (LIMIT, offset)).read()

            titles = json.loads(titles_json)
            with open ('tmp/debug.json', 'w') as debugf:
                debugf.write(json.dumps(titles, indent=4, sort_keys=True))

            cnt = 0

            if isinstance(titles['books'], list):
                for book in titles['books']:
                    books.append(book)
                    cnt += 1
            else:
                for k in titles['books']:
                    books.append(titles['books'][k])
                    cnt += 1

            # if cnt < LIMIT:
            #     with open ('tmp/debug2.json', 'w') as debugf:
            #         debugf.write(titles_json)
            #     sys.exit(1)


            offset += LIMIT

            with open(DBFN, 'w') as dbf:
                dbf.write(json.dumps(books))
    except:
        print "EXCEPTION"
        traceback.print_exc()

else:

    with open(DBFN, 'r') as dbf:
        books = json.loads(dbf.read())

def mangle_title(title):
    res = u""
    for c in title:
        if c == u" ":
            res += u"-"
        elif c.isalnum():
            res += c
    return res

def mangle_reader(title):
    res = u""
    for c in title:
        if c.isalnum():
            res += c.lower()
    return res

#
# filter books of interest, generate download script
#

total_time = 0

scriptfn = '%s/download.sh' % ZIPDIR

with open(scriptfn, 'w', 0755) as scriptf:

    scriptf.write("#!/bin/bash\n\n")

    for book in books:

        # scriptf.write('%s\n' % book['title'])

        # if 'eyre' in book['title'].lower():
        #     print repr(book)

        if book['language'] != 'German':
            continue

        if not book['url_zip_file']:
            continue

        print book['id'], book['title'], book['totaltime']
        print "    ", book['url_librivox']
        print "    ", book['url_zip_file']

        total_time += int(book['totaltimesecs'])

        scriptf.write('wget "%s" &\n' % book['url_zip_file'])

    scriptf.write("\nwait\n")

print 
print "total time: %f h in %d books" % (float(total_time) / 3600.0, len(books))
print "%s written." % scriptfn
print

# #
# # download book(s)
# #
# 
# for book_id in args[1:]:
# 
#     book = books[book_id]
# 
#     title = book['id'] + '-' + mangle_title(book['title'])
# 
#     print book['id'], title, book['totaltime']
#     print "    ", book['url_project']
# 
# #     for section in book['sections']:
# # 
# #         stitle   = section['title']
# #         sn       = section['section_number']
# #         readers  = section['readers']
# #         if not readers:
# #             continue
# #         reader   = mangle_reader(readers[0]['display_name'])
# #         playtime = int(section['playtime'])
# #         url      = section['listen_url']
# #         if not url:
# #             continue
# # 
# #         total_time += playtime
# # 
# #         dirfn = '%s/%s' % (dstdirfn, title)
# #         misc.mkdirs(dirfn)
# # 
# #         wavfn = '%s/%s/%s-%s-%s.wav' % (dstdirfn, title, reader, title, sn)
# #         print total_time, wavfn, playtime
# #         print url
    
