#!/bin/bash

SPEECH_ARCH=/home/bofh/projects/ai/data/speech/arc
SPEECH_CORPORA=/home/bofh/projects/ai/data/speech/corpora

#
# english
#

cd "${SPEECH_ARCH}/voxforge_en"

rm index.*
wget -c -r -nd -l 1 -np http://www.repository.voxforge1.org/downloads/SpeechCorpus/Trunk/Audio/Main/16kHz_16bit/

cd "${SPEECH_CORPORA}/voxforge_en"
for i in ${SPEECH_ARCH}/voxforge_en/*.tgz ; do

    echo "tar xfz $i"
    tar xfz $i

done

#
# german
#

cd "${SPEECH_ARCH}/voxforge_de"

rm index.*
wget -c -r -nd -l 1 -np http://www.repository.voxforge1.org/downloads/de/Trunk/Audio/Main/16kHz_16bit/
# rm openpento*

cd "${SPEECH_CORPORA}/voxforge_de"
for i in ${SPEECH_ARCH}/voxforge_de/*.tgz ; do

    echo "tar xfz $i"
    tar xfz $i

done

