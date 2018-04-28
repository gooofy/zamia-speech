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
# retrieve audiobooks from librivox, unpack individual ones if needed
#

import os
import sys
import logging
import traceback
import codecs
import urllib2
import json

from optparse import OptionParser
from zipfile  import ZipFile

from nltools  import misc

DBFN          = 'data/dst/speech/de/librivox.json'
LIMIT         = 50

#
# init 
#

misc.init_app ('abook-librivox')

config = misc.load_config ('.speechrc')

speech_arc_dir = config.get("speech", "speech_arc")
librivox_zipdir = '%s/librivox_de' % speech_arc_dir

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

    print "loading %s..." % DBFN

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

scriptfn = 'abook/librivox-download.sh'

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

#
# extract wav audios of book(s), if requested
#

for book_id in args[1:]:

    for book in books:
        if book['id'] != book_id:
            continue

        title = book['id'] + '-' + mangle_title(book['title'])

        print book['id'], title, book['totaltime']
        print "    ", book['url_project']

        book_dir = 'abook/in/librivox/%s' % title
        misc.mkdirs(book_dir)

        print "%s created." % book_dir

        url = book['url_zip_file']
        zipfilefn = '%s/%s' % (librivox_zipdir, url[url.rfind("/")+1:])

        print "Extracting audio from zip file %s ..." % zipfilefn

        with ZipFile(zipfilefn, 'r') as zipfile:
      
            mp3s = []
            for mp3fn in sorted (zipfile.namelist()):
                if not mp3fn.endswith('.mp3'):
                    continue
                mp3s.append(mp3fn)

            # print mp3s
 
            for i, section in enumerate(book['sections']):

                stitle   = section['title']
                sn       = section['section_number']
                readers  = section['readers']
                if not readers:
                    continue
                reader   = mangle_reader(readers[0]['display_name'])

                wavfn = '%s/%s-%s-%s.wav' % (book_dir, reader, title, sn)

                if not os.path.exists(wavfn):

                    mp3fn = mp3s[i]

                    print "Extracting %s -> %s..." % (mp3fn, wavfn)

                    with zipfile.open(mp3fn, 'r') as mp3f, \
                         open('abook/_tmp.mp3', 'w') as mp3tmpf:
                        mp3tmpf.write(mp3f.read())

                    cmd = 'ffmpeg -i abook/_tmp.mp3 abook/_tmp.wav'
                    os.system(cmd)
                    cmd = 'sox abook/_tmp.wav -r 16000 -c 1 %s' % wavfn
                    os.system(cmd)
                    cmd = 'rm abook/_tmp.wav abook/_tmp.mp3'
                    os.system(cmd)

                txtfn = '%s/%s-%s-%s.txt' % (book_dir, reader, title, sn)

                if not os.path.exists(txtfn):

                    print "Creating empty %s ..." % txtfn

                    with open(txtfn, 'w') as txtf:
                        txtf.write('')


