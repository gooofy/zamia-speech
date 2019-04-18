#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 by Marc Puels
# Copyright 2016 by G.Bartsch
# Copyright 2015 Language Technology, Technische Universitaet Darmstadt (author: Benjamin Milde)
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

import logging
import codecs
from bs4 import BeautifulSoup
import shutil
import sys

import plac
from pathlib2 import Path

from nltools import misc

#
# convert german-speechdata-package-v2 to voxforge-style packages
#

@plac.annotations(
    verbose=("Enable verbose logging", "flag", "v"))
def main(verbose=False):
    """Convert gspv2 corpus to the VoxForge corpus format

    The variable `speech_arc` in ~/.speechrc must point to a folder
    gspv2 which is used as the source containing the original gspv2 corpus, 
    i.e. containing the subfolders dev, test, and train.

    The variable `speech_corpora` in ~/.speechrc must point to a folder
    where the resulting corpus should be written. The script will create
    a subfolder gspv2 here for the resulting voxforge-formatted data.
    """
    misc.init_app('speech_audio_scan')
    config = misc.load_config('.speechrc')

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    speech_arc_dir     = Path(config.get("speech", "speech_arc"))
    speech_corpora_dir = Path(config.get("speech", "speech_corpora"))
    src_root_dir = speech_arc_dir / "gspv2"
    dst_root_dir = speech_corpora_dir / "gspv2"

    exit_if_dst_root_dir_exists(dst_root_dir)

    speakers = set()
    speaker_gender = {}

    for folder in ['train', 'test', 'dev']:
        destdir = dst_root_dir

        src_dir = src_root_dir / folder

        num_files = len([f for f in src_dir.glob("*.xml")])

        cnt_files = 0

        for xml_path in src_dir.glob("*.xml"):
            f = str(xml_path)

            cnt_files += 1

            fbase = f[0:len(f) - 4]

            with codecs.open(f, 'r', 'utf-8') as xmlfile:
                # remove urls
                text = xmlfile.read()
                soup = BeautifulSoup(text)
                sentence = (soup.recording.sentence.string).strip()
                cleaned_sentence = (
                    soup.recording.cleaned_sentence.string).strip()
                sentence_id = int(
                    (soup.recording.sentence_id.string).strip())

                speaker_id = (soup.recording.speaker_id.string).strip()
                gender = (soup.recording.gender.string).strip()
                name = 'gsp%s' % speaker_id.replace('-', '')
                speakerdir = destdir / (name + "-1")

                if not speaker_id in speakers:
                    speakers.add(speaker_id)
                    speaker_gender[name] = \
                        'm' if gender == 'male' else 'f'
                    (speakerdir / "wav").mkdir(parents=True, exist_ok=True)
                    (speakerdir / "etc").mkdir(parents=True, exist_ok=True)

                for mic in ['Yamaha', 'Kinect-Beam', 'Kinect-RAW',
                            'Realtek', 'Samson']:
                    srcaudiofn = src_dir / ('%s_%s.wav' % (fbase, mic))

                    if not srcaudiofn.is_file():
                        continue

                    audiofn = Path('%s-%s' % (fbase, mic)).name
                    dstaudiofn = speakerdir / "wav" / (audiofn + ".wav")


                    logging.info('%5d/%5d %s %s %s' % (
                        cnt_files, num_files, name, audiofn,
                        str(srcaudiofn)))

                    prompts_orig = speakerdir / "etc" / "prompts-original"
                    with open(str(prompts_orig), 'a') as promptsf:
                        promptsf.write((u'%s %s\n' % (
                        audiofn, cleaned_sentence)).encode('utf8'))

                    copy_file(str(srcaudiofn), str(dstaudiofn))

    # Usually, you don't to run this code. It was taken as the source for
    # data/src/speech/gspv2/spk2gender.
    #with open('gender.txt', 'w') as genderf:
    #    for name in sorted(speaker_gender.keys()):
    #        genderf.write('%s %s\n' % (name, speaker_gender[name]))


def exit_if_dst_root_dir_exists(dst_root_dir):
    if dst_root_dir.is_dir():
        logging.error(
            "Destination folder {} already exists. Please either rename or "
            "remove it.".format(dst_root_dir))
        sys.exit(1)


def copy_file (src, dst):
    logging.debug("copying %s to %s" % (src, dst))
    shutil.copy(src, dst)


if __name__ == "__main__":
    plac.call(main)
