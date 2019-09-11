#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 by Paul Guyot
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# convert Transcriber files to voxforge-style packages
#
# Import .trs and .wav/.mp3 files. File names should match. A heuristic is used
# when they do not match exactly, however it may fail or process the wrong file.
# Run with -n to check all files can be read and they match.
# Volume is adjusted on a per-file basis.
# Turns with no speaker attribute or with several speakers are ignored.

import sys
import os
import codecs
import traceback
import logging
import re
import xml.etree.ElementTree as ET
import multiprocessing as mp

from difflib import SequenceMatcher

from optparse               import OptionParser
from nltools                import misc

PROC_TITLE        = 'trs_to_vf'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options] corpus")

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

parser.add_option ("-n", "--dry", action="store_true", dest="dry", 
                   help="check files, do not actually generate files")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if len(args)<1:
    parser.print_usage()
    sys.exit(1)

corpus_name = args[0]

#
# config
#

config = misc.load_config ('.speechrc')
speech_arc     = config.get("speech", "speech_arc")
speech_corpora = config.get("speech", "speech_corpora")

# iterate on every trs file in arc/corpus_name/

class DoctypeAwareTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        self.__doctype_name = name
        self.__doctype_system = system
    
    def valid(self):
        return self.__doctype_name == 'Trans' and (self.__doctype_system == 'trans-14.dtd' or self.__doctype_system == 'trans-13.dtd')

def seconds_to_ffmpeg_ts(seconds):
    minutes=int(seconds/60)
    seconds=seconds-minutes*60
    hours=int(minutes/60)
    minutes=minutes-hours*60
    return '{:02d}:{:02d}:{:06.3f}'.format(hours, minutes, seconds)

def get_volume(recording):
    cmd="ffmpeg -hide_banner -i {recording} -filter:a volumedetect -f null /dev/null 2>&1 | grep max_volume | awk '{{ print $5 }}'".format(recording=recording)
    volume=os.popen(cmd).read()
    volume=-float(volume)
    return volume
    
def extract_wav(recording, volume, wav, startTime, endTime):
    if os.path.exists(wav):
        logging.debug('Skipping {wav} as it already exists'.format(wav=wav))
        return
    startTimeF = float(startTime)
    endTimeF = float(endTime)
    duration = endTimeF - startTimeF
    startTimeFormatted=seconds_to_ffmpeg_ts(startTimeF)
    durationFormatted=seconds_to_ffmpeg_ts(duration)
    cmd='ffmpeg -y -hide_banner -loglevel panic -i {recording} -ss {startTimeFormatted} -t {durationFormatted} -filter:a "volume={volume}dB" -ac 1 -ar 16k {wav}'.format(recording=recording, startTimeFormatted=startTimeFormatted, durationFormatted=durationFormatted, volume=volume, wav=wav)
    os.system(cmd)

def find_recording(dir, root_filename):
    for suffix in ['.wav', '.WAV', '.mp3', '-v2.wav', '-v2.mp3']:
        recording='{dir}/{root_filename}{suffix}'.format(dir=dir, root_filename=root_filename, suffix=suffix)
        if os.path.isfile(recording):
            return recording
    best_candidate=None
    best_candidate_ratio=0.9
    for recording_filename in os.listdir(dir):
        if recording_filename.endswith(".mp3") or recording_filename.endswith(".wav"):
            basename=recording_filename[:-4]
            candidate_ratio = SequenceMatcher(None, basename, root_filename).ratio()
            if candidate_ratio > best_candidate_ratio:
                best_candidate=recording_filename
                best_candidate_ratio=candidate_ratio
    if best_candidate!=None:
        logging.warning('{root_filename}: using file {recording}, ratio={ratio}'.format(root_filename=root_filename, recording=best_candidate, ratio=best_candidate_ratio))
        return '{dir}/{best_candidate}'.format(dir=dir, best_candidate=best_candidate)
    logging.error('{root_filename}: cannot find recording file'.format(root_filename=root_filename))
    return None

def process_dir(pool, dir):
    totalDuration=0
    for filename in os.listdir(dir):
        path='%s/%s' % (dir, filename)
        if os.path.isdir(path):
            totalDuration=totalDuration+process_dir(pool, path)
        elif os.path.isfile(path) and filename.endswith(".trs"):
            corpus_filename=filename
            corpus_filepath=path
            logging.info('Processing {corpus_filename}'.format(corpus_filename=corpus_filename))
            root_filename=corpus_filename[:-4]
            if root_filename.endswith("-v2"):
                root_filename=root_filename[:-3]
            recording=find_recording(dir, root_filename)
            if recording == None:
                continue
            if options.dry and not options.verbose:
                volume=None
            else:
                volume=get_volume(recording)
            treebuilder = DoctypeAwareTreeBuilder()
            parser = ET.XMLParser(target=treebuilder)
            tree = ET.parse(corpus_filepath, parser=parser)
            if not treebuilder.valid():
                logging.error('{corpus_filepath}: Invalid DOCTYPE, was expecting <!DOCTYPE Trans SYSTEM "trans-13.dtd"> or <!DOCTYPE Trans SYSTEM "trans-14.dtd">'.format(corpus_filepath=corpus_filepath))
                continue
            root = tree.getroot()
            speakerst = {}
            for speakers in root.findall('Speakers'):
                for speaker in speakers.findall('Speaker'):
                    speakerid = speaker.attrib['id']
                    speakername = speaker.attrib['name']
                    speakerst[speakerid] = re.sub(r'[ ()/-]', '', speakername)
            for episode in root.findall('Episode'):
                for section in episode.findall('Section'):
                    for turn in section.findall('Turn'):
                        if not 'speaker' in turn.attrib:
                            logging.warning('{corpus_filename}: Turn element missing speaker attribute'.format(corpus_filename=corpus_filename))
                            continue
                        speakerid = turn.attrib['speaker']
                        if speakerid in speakerst:  # skip cases with several speakers
                            startTime = turn.attrib['startTime']
                            endTime = turn.attrib['endTime']
                            speakername = speakerst[speakerid]
                            startTimeF = float(startTime)
                            endTimeF = float(endTime)
                            duration = endTimeF - startTimeF
                            wavdir='{corpora}/{corpus_name}/{spk}-{name}/wav/'.format(corpora=speech_corpora, corpus_name=corpus_name, name=root_filename, spk=speakername)
                            etcdir='{corpora}/{corpus_name}/{spk}-{name}/etc/'.format(corpora=speech_corpora, corpus_name=corpus_name, name=root_filename, spk=speakername)
                            if not options.dry:
                                if not os.path.exists(wavdir):
                                    os.makedirs(wavdir)
                                if not os.path.exists(etcdir):
                                    os.makedirs(etcdir)
                            text=" ".join(turn.itertext()).replace('\n', '').replace('  ', ' ')
                            if re.search(r'\w', text, re.I) != None and re.search(r'¤', text) == None:
                                uttid='{spk}-{name}-{startTime}-{endTime}'.format(name=root_filename, spk=speakername, startTime=startTime, endTime=endTime)
                                if not options.dry:
                                    with codecs.open('{etcdir}/prompts-original'.format(etcdir=etcdir), 'a', 'utf8') as promptsf:
                                        promptsf.write('%s %s\n' % (uttid, text))
                                wav='{corpora}/{corpus_name}/{spk}-{name}/wav/{uttid}.wav'.format(corpora=speech_corpora, corpus_name=corpus_name, name=root_filename, spk=speakername, uttid=uttid)
                                if options.dry:
                                    logging.debug('Would convert {recording} from {startTime} to {endTime} to {wav} with volume gain of {volume}'.format(recording=recording, volume=volume, wav=wav, startTime=startTime, endTime=endTime))
                                else:
                                    logging.debug('Convert {recording} from {startTime} to {endTime} to {wav} with volume gain of {volume}'.format(recording=recording, volume=volume, wav=wav, startTime=startTime, endTime=endTime))
                                    pool.apply_async(extract_wav, args=(recording, volume, wav, startTime, endTime))
                                totalDuration=totalDuration+duration
                            else:
                                logging.debug('Skipping empty/anonymized text={text}'.format(text=text))
    return totalDuration

pool = mp.Pool(mp.cpu_count())
arc_corpus_dir='{speech_arc}/{corpus_name}'.format(speech_arc=speech_arc, corpus_name=corpus_name)
totalDuration=process_dir(pool, arc_corpus_dir)
logging.info('Total duration: {formatted}'.format(formatted=seconds_to_ffmpeg_ts(totalDuration)))
pool.close()
pool.join()
