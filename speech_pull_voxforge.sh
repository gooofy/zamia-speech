#!/bin/bash

#
# english
#

cd /home/bofh/projects/ai/data/speech/en/voxforge

pushd audio-arc

rm index.*
wget -c -r -nd -l 1 -np http://www.repository.voxforge1.org/downloads/SpeechCorpus/Trunk/Audio/Main/16kHz_16bit/

popd

pushd audio
for i in ../audio-arc/*.tgz ; do

    echo $i

    tar xfz $i

done

popd

#
# german
#

cd /home/bofh/projects/ai/data/speech/de/voxforge

pushd audio-arc

rm index.*
wget -c -r -nd -l 1 -np http://www.repository.voxforge1.org/downloads/de/Trunk/Audio/Main/16kHz_16bit/
# rm openpento*

popd

pushd audio
for i in ../audio-arc/*.tgz ; do

    echo $i

    tar xfz $i

done

popd

