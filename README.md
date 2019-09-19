# Zamia Speech

Python scripts to compute audio and language models from voxforge.org speech data and many sources.
Models that can be built include:

* Kaldi nnet3 chain audio models
* KenLM language models in ARPA format
* sequitur g2p models
* wav2letter++ models

*Important*: Please note that these scripts form in no way a complete application ready for end-user consumption.
However, if you are a developer interested in natural language processing you may find some of them useful.
Contributions, patches and pull requests are very welcome.

At the time of this writing, the scripts here are focused on building the English and German VoxForge models. 
However, there is no reason why they couldn't be used to build other language models as well, feel free to 
contribute support for those.


Table of Contents
=================

   * [Zamia Speech](#zamia-speech)
   * [Table of Contents](#table-of-contents)
   * [Download](#download)
      * [ASR Models](#asr-models)
      * [IPA Dictionaries (Lexicons)](#ipa-dictionaries-lexicons)
      * [G2P Models](#g2p-models)
      * [Language Models](#language-models)
      * [Code](#code)
   * [Get Started with our Pre-Trained Models](#get-started-with-our-pre-trained-models)
      * [Installation](#installation)
         * [Raspbian 9 (stretch) on a Raspberry Pi 2/3](#raspbian-9-stretch-on-a-raspberry-pi-23)
         * [Raspberry Pi Zero](#raspberry-pi-zero)
         * [Debian 9 (stretch, amd64)](#debian-9-stretch-amd64)
         * [CentOS 7 (amd64)](#centos-7-amd64)
      * [Run Example Applications](#run-example-applications)
         * [Wave File Decoding Demo](#wave-file-decoding-demo)
         * [Live Mic Demo](#live-mic-demo)
   * [Get Started with a Demo STT Service Packaged in Docker](#get-started-with-a-demo-stt-service-packaged-in-docker)
   * [Requirements](#requirements)
   * [Setup Notes](#setup-notes)
      * [~/.speechrc](#speechrc)
      * [tmp directory](#tmp-directory)
   * [Speech Corpora](#speech-corpora)
      * [Adding Artificial Noise or Other Effects](#adding-artificial-noise-or-other-effects)
   * [Text Corpora](#text-corpora)
   * [Language Model](#language-model)
      * [English](#english)
      * [German](#german)
      * [French](#french)
   * [Submission Review and Transcription](#submission-review-and-transcription)
   * [Lexica/Dictionaries](#lexicadictionaries)
      * [Sequitur G2P](#sequitur-g2p)
      * [Manual Editing](#manual-editing)
      * [Wiktionary](#wiktionary)
   * [Kaldi Models (recommended)](#kaldi-models-recommended)
      * [English NNet3 Chain Models](#english-nnet3-chain-models)
      * [German NNet3 Chain Models](#german-nnet3-chain-models)
      * [Model Adaptation](#model-adaptation)
   * [wav2letter   models](#wav2letter-models)
      * [English Wav2letter Models](#english-wav2letter-models)
      * [German Wav2letter Models](#german-wav2letter-models)
      * [auto-reviews using wav2letter](#auto-reviews-using-wav2letter)
   * [Audiobook Segmentation and Transcription (Manual)](#audiobook-segmentation-and-transcription-manual)
      * [(0/3) Convert Audio to WAVE Format](#03-convert-audio-to-wave-format)
      * [(1/3) Convert Audio to 16kHz mono](#13-convert-audio-to-16khz-mono)
      * [(2/3) Split Audio into Segments](#23-split-audio-into-segments)
      * [(3/3) Transcribe Audio](#33-transcribe-audio)
   * [Audiobook Segmentation and Transcription (kaldi)](#audiobook-segmentation-and-transcription-kaldi)
      * [Directory Layout](#directory-layout)
      * [(1/4) Preprocess the Transcript](#14-preprocess-the-transcript)
      * [(2/4) Model adaptation](#24-model-adaptation)
      * [(3/4) Auto-Segment using Kaldi](#34-auto-segment-using-kaldi)
      * [(4/4) Retrieve Segmentation Result](#44-retrieve-segmentation-result)
   * [Training Voices for Zamia-TTS](#training-voices-for-zamia-tts)
      * [Tacotron 2](#tacotron-2)
      * [Tacotron](#tacotron)
   * [Model Distribution](#model-distribution)
   * [License](#license)
   * [Authors](#authors)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc.go)

Download
========

We have various models plus source code and binaries for the tools used to build these models
available for download. Everything is free and open source.

All our model and data downloads can be found here: [Downloads](http://goofy.zamia.org/zamia-speech/)

ASR Models 
----------

Our pre-built ASR models can be downloaded here: [ASR Models](http://goofy.zamia.org/zamia-speech/asr-models/)

+ Kaldi ASR, English:
    + `kaldi-generic-en-tdnn_f`
      Large nnet3-chain factorized TDNN model, trained on ~1200 hours of audio. Has decent background noise resistance and can
      also be used on phone recordings. Should provide the best accuracy but is a bit more resource intensive than the
      other models.
    + `kaldi-generic-en-tdnn_sp`
      Large nnet3-chain model, trained on ~1200 hours of audio. Has decent background noise resistance and can
      also be used on phone recordings. Less accurate but also slightly less resource intensive than the `tddn_f` model.
    + `kaldi-generic-en-tdnn_250`
      Same as the larger models but less resource intensive, suitable for use in embedded applications (e.g. a RaspberryPi 3).
    + `kaldi-generic-en-tri2b_chain`
      GMM Model, trained on the same data as the above two models - meant for auto segmentation tasks.
+ Kaldi ASR, German:
    + `kaldi-generic-de-tdnn_f`
      Large nnet3-chain model, trained on ~400 hours of audio. Has decent background noise resistance and can
      also be used on phone recordings.
    + `kaldi-generic-de-tdnn_250`
      Same as the large model but less resource intensive, suitable for use in embedded applications (e.g. a RaspberryPi 3).
    + `kaldi-generic-de-tri2b_chain`
      GMM Model, trained on the same data as the above two models - meant for auto segmentation tasks.
+ wav2letter++, German:
    + `w2l-generic-de`
      Large model, trained on ~400 hours of audio. Has decent background noise resistance and can
      also be used on phone recordings.

*NOTE*: It is important to realize that these models can and should be adapted to your application domain. See 
        [Model Adaptation](#model-adaptation) for details.

IPA Dictionaries (Lexicons)
---------------------------

Our dictionaries can be downloaded here: [Dictionaries](https://github.com/gooofy/zamia-speech/tree/master/data/src/dicts)

+ IPA UTF-8, English:
    + `dict-en.ipa`
      Based on CMUDict with many additional entries generated via Sequitur G2P.
+ IPA UTF-8, German:
    + `dict-de.ipa`
      Created manually from scratch with many additional auto-reviewed entries extracted from Wiktionary.

G2P Models 
----------

Our pre-built G2P models can be downloaded here: [G2P Models](http://goofy.zamia.org/zamia-speech/g2p/)

+ Sequitur, English:
    + ` sequitur-dict-en.ipa`
      Sequitur G2P model trained on our English IPA dictionary (UTF8).
+ Sequitur, German:
    + ` sequitur-dict-de.ipa`
      Sequitur G2P model trained on our German IPA dictionary (UTF8).

Language Models
---------------

Our pre-built ARPA language models can be downloaded here: [Language Models](http://goofy.zamia.org/zamia-speech/lm/)

+ KenLM, order 4, English, ARPA:
    + `generic_en_lang_model_small`
+ KenLM, order 6, English, ARPA:
    + `generic_en_lang_model_large`
+ KenLM, order 4, German, ARPA:
    + `generic_de_lang_model_small`
+ KenLM, order 6, German, ARPA:
    + `generic_de_lang_model_large`

Code
----

* [Zamia-Speech](https://github.com/gooofy/zamia-speech) 
    where we host all our scripts and other sources used to build our models. 
* [py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr) 
    Python wrapper around Kaldi's nnet3-chain decoder complete with example
    scripts on how to use our models in your application.
* [Binary AI Packages](http://goofy.zamia.org/repo-ai/)
    + [Raspbian APT Repo](http://goofy.zamia.org/repo-ai/raspbian/stretch/armhf)
        Binary packages in Debian format for Raspbian 9 (stretch, armhf, Raspberry Pi 2/3)
    + [Debian APT Repo](http://goofy.zamia.org/repo-ai/debian/stretch/amd64)
        Binary packages in Debian format for Debian 9 (stretch, amd64)
    + [CentOS YUM Repo](http://goofy.zamia.org/repo-ai/centos/7/x86_64/)
        Binary packages in RPM format for CentOS 7 (x86_64)
* [Source AI Packages](http://goofy.zamia.org/repo-ai/)
    + [CentOS 7](http://goofy.zamia.org/repo-ai/centos/7/SRPMS/)
        Source packages in SRPM format for CentOS 7

Get Started with our Pre-Trained Models 
=======================================

Installation
------------

### Raspbian 9 (stretch) on a Raspberry Pi 2/3

Setup apt-source and install packages:

```bash
# execute with root permissions (sudo -i):

echo "deb http://goofy.zamia.org/repo-ai/raspbian/stretch/armhf/ ./" >/etc/apt/sources.list.d/zamia-ai.list
wget -qO - http://goofy.zamia.org/repo-ai/raspbian/stretch/armhf/bofh.asc | sudo apt-key add -
apt-get update
apt-get install kaldi-chain-zamia-speech-de kaldi-chain-zamia-speech-en python-kaldiasr python-nltools pulseaudio-utils pulseaudio
```

### Raspberry Pi Zero

Paul Guyot has built kaldi for the rpi zero along with our python wrappers:

https://github.com/pguyot/kaldi/releases
https://github.com/pguyot/py-kaldi-asr/releases/tag/v0.5.2

### Debian 9 (stretch, amd64)

Setup apt-source and install packages:

```bash
# execute with root permissions (sudo -i):

apt-get install apt-transport-https
echo "deb http://goofy.zamia.org/repo-ai/debian/stretch/amd64/ ./" >/etc/apt/sources.list.d/zamia-ai.list
wget -qO - http://goofy.zamia.org/repo-ai/debian/stretch/amd64/bofh.asc | sudo apt-key add -
apt-get update
apt-get install kaldi-chain-zamia-speech-de kaldi-chain-zamia-speech-en python-kaldiasr python-nltools pulseaudio-utils pulseaudio
```

### CentOS 7 (amd64)

Setup yum repo and install packages:

```bash
# execute with root permissions (sudo -i):

cd /etc/yum.repos.d
wget http://goofy.zamia.org/zamia-speech/misc/zamia-ai-centos.repo
yum install kaldi-chain-zamia-speech-de kaldi-chain-zamia-speech-en python-kaldiasr python-nltools pulseaudio-utils pulseaudio
```

alternatively you can download RPMs manually here:
* [x86\_64](http://goofy.zamia.org/repo-ai/centos/7/x86_64/)
* [SRPMS](http://goofy.zamia.org/repo-ai/centos/7/SRPMS/)

Run Example Applications
------------------------

### Wave File Decoding Demo

Download a few sample wave files

```bash
$ wget http://goofy.zamia.org/zamia-speech/misc/demo_wavs.tgz
--2018-06-23 16:46:28--  http://goofy.zamia.org/zamia-speech/misc/demo_wavs.tgz
Resolving goofy.zamia.org (goofy.zamia.org)... 78.47.65.20
Connecting to goofy.zamia.org (goofy.zamia.org)|78.47.65.20|:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 619852 (605K) [application/x-gzip]
Saving to: ‘demo_wavs.tgz’

demo_wavs.tgz                     100%[==========================================================>] 605.32K  2.01MB/s    in 0.3s    

2018-06-23 16:46:28 (2.01 MB/s) - ‘demo_wavs.tgz’ saved [619852/619852]
```

unpack them:

```bash
$ tar xfvz demo_wavs.tgz
demo1.wav
demo2.wav
demo3.wav
demo4.wav
```

download the demo program 


```bash
$ wget http://goofy.zamia.org/zamia-speech/misc/kaldi_decode_wav.py
--2018-06-23 16:47:53--  http://goofy.zamia.org/zamia-speech/misc/kaldi_decode_wav.py
Resolving goofy.zamia.org (goofy.zamia.org)... 78.47.65.20
Connecting to goofy.zamia.org (goofy.zamia.org)|78.47.65.20|:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 2469 (2.4K) [text/plain]
Saving to: ‘kaldi_decode_wav.py’

kaldi_decode_wav.py               100%[==========================================================>]   2.41K  --.-KB/s    in 0s      

2018-06-23 16:47:53 (311 MB/s) - ‘kaldi_decode_wav.py’ saved [2469/2469]
```

now run kaldi automatic speech recognition on the demo wav files:

```bash
$ python kaldi_decode_wav.py -v demo?.wav
DEBUG:root:/opt/kaldi/model/kaldi-generic-en-tdnn_sp loading model...
DEBUG:root:/opt/kaldi/model/kaldi-generic-en-tdnn_sp loading model... done, took 1.473226s.
DEBUG:root:/opt/kaldi/model/kaldi-generic-en-tdnn_sp creating decoder...
DEBUG:root:/opt/kaldi/model/kaldi-generic-en-tdnn_sp creating decoder... done, took 0.143928s.
DEBUG:root:demo1.wav decoding took     0.37s, likelyhood: 1.863645
i cannot follow you she said 
DEBUG:root:demo2.wav decoding took     0.54s, likelyhood: 1.572326
i should like to engage just for one whole life in that 
DEBUG:root:demo3.wav decoding took     0.42s, likelyhood: 1.709773
philip knew that she was not an indian 
DEBUG:root:demo4.wav decoding took     1.06s, likelyhood: 1.715135
he also contented that better confidence was established by carrying no weapons 
```

### Live Mic Demo

Determine the name of your pulseaudio mic source:

```bash
$ pactl list sources
Source #0
    State: SUSPENDED
    Name: alsa_input.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-mono
    Description: CM108 Audio Controller Analog Mono
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

download and run demo:

```bash
$ wget 'http://goofy.zamia.org/zamia-speech/misc/kaldi_decode_live.py'

$ python kaldi_decode_live.py -s 'CM108'
Kaldi live demo V0.2
Loading model from /opt/kaldi/model/kaldi-generic-en-tdnn_250 ...
Please speak.
hallo computer                      
switch on the radio please                      
please switch on the light                      
what about the weather in stuttgart                     
how are you                      
thank you                      
good bye 
```

Get Started with a Demo STT Service Packaged in Docker
======================================================

To start the STT service on your local machine, execute:

```bash
$ docker pull quay.io/mpuels/docker-py-kaldi-asr-and-model:kaldi-generic-en-tdnn_sp-r20180611
$ docker run --rm -p 127.0.0.1:8080:80/tcp quay.io/mpuels/docker-py-kaldi-asr-and-model:kaldi-generic-en-tdnn_sp-r20180611
```

To transfer an audio file for transcription to the service, in a second
terminal, execute:

```bash
$ git clone https://github.com/mpuels/docker-py-kaldi-asr-and-model.git
$ conda env create -f environment.yml
$ source activate py-kaldi-asr-client
$ ./asr_client.py asr.wav
INFO:root: 0.005s:  4000 frames ( 0.250s) decoded, status=200.
...
INFO:root:19.146s: 152000 frames ( 9.500s) decoded, status=200.
INFO:root:27.136s: 153003 frames ( 9.563s) decoded, status=200.
INFO:root:*****************************************************************
INFO:root:** wavfn         : asr.wav
INFO:root:** hstr          : speech recognition system requires training where individuals to exercise political system
INFO:root:** confidence    : -0.578844
INFO:root:** decoding time :    27.14s
INFO:root:*****************************************************************
```

The Docker image in the example above is the result of stacking 4 images on top
of each other:

- docker-py-kaldi-asr-and-model: [Source](https://github.com/mpuels/docker-py-kaldi-asr-and-model), [Image](https://quay.io/repository/mpuels/docker-py-kaldi-asr-and-model)

- docker-py-kaldi-asr: [Source](https://github.com/mpuels/docker-py-kaldi-asr), [Image](https://quay.io/repository/mpuels/docker-py-kaldi-asr)

- docker-kaldi-asr: [Source](https://github.com/mpuels/docker-kaldi-asr), [Image](https://quay.io/repository/mpuels/docker-kaldi-asr)

- debian:8: https://hub.docker.com/_/debian/


Requirements
============

*Note*: probably incomplete.

* Python 2.7 with nltk, numpy, ...
* KenLM
* kaldi
* wav2letter++
* py-nltools
* sox

Setup Notes
===========

Just some rough notes on the environment needed to get these scripts to run. This is in no way a complete set of
instructions, just some hints to get you started.

`~/.speechrc`
-------------

```ini
[speech]
vf_login              = <your voxforge login>

speech_arc            = /home/bofh/projects/ai/data/speech/arc
speech_corpora        = /home/bofh/projects/ai/data/speech/corpora

kaldi_root            = /apps/kaldi-cuda

; facebook's wav2letter++
w2l_env_activate      = /home/bofh/projects/ai/w2l/bin/activate
w2l_train             = /home/bofh/projects/ai/w2l/src/wav2letter/build/Train
w2l_decoder           = /home/bofh/projects/ai/w2l/src/wav2letter/build/Decoder

wav16                 = /home/bofh/projects/ai/data/speech/16kHz
noise_dir             = /home/bofh/projects/ai/data/speech/corpora/noise

europarl_de           = /home/bofh/projects/ai/data/corpora/de/europarl-v7.de-en.de
parole_de             = /home/bofh/projects/ai/data/corpora/de/German Parole Corpus/DE_Parole/

europarl_en           = /home/bofh/projects/ai/data/corpora/en/europarl-v7.de-en.en
cornell_movie_dialogs = /home/bofh/projects/ai/data/corpora/en/cornell_movie_dialogs_corpus
web_questions         = /home/bofh/projects/ai/data/corpora/en/WebQuestions
yahoo_answers         = /home/bofh/projects/ai/data/corpora/en/YahooAnswers

europarl_fr           = /home/bofh/projects/ai/data/corpora/fr/europarl-v7.fr-en.fr
est_republicain       = /home/bofh/projects/ai/data/corpora/fr/est_republicain.txt

wiktionary_de         = /home/bofh/projects/ai/data/corpora/de/dewiktionary-20180320-pages-meta-current.xml

[tts]
host                  = localhost
port                  = 8300
```

tmp directory
-------------

Some scripts expect al local `tmp` directory to be present, located in the same directory where all the scripts live, i.e.

```bash
mkdir tmp
```


Speech Corpora
==============

The following list contains speech corpora supported by this script collection.

- [CFPP2000, Corpus de Français Parlé Parisien des années 2000 (French, 47 hours)](http://cfpp2000.univ-paris3.fr/Corpus.html):
    + Download `.mp3` or `.wav` files as well as `.trs` files.
    + Rename files so that each `.trs` file has the same basename of
      corresponding `.wav` or `.mp3` file
    + Put audio and transcription files in subdirectory `cfpp2000` of
      `<~/.speechrc:speech_arc>`.
    + Then run run the script `./import_trs.py cfpp2000` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/cfpp2000`.

- [CLAPI, Corpus de LAngue Parlée en Interaction (French, 7 hours)](http://clapi.ish-lyon.cnrs.fr/):
    + Download `.mp4`/`.wav` files as well as `.trs` files (favor "orthographe standard" trs files).
      At least two trs files are bogus and should not be used
      ("Boulangerie rurale C21-C41 orthographe standa -trs (trs)" and "Bureau CPE - bagarre -trs (trs)")
      At least three `.wav` files are corrupt, prefer `.mp4` videos.
    + Rename files so that each `.trs` file has the same basename of
      corresponding `.wav` file
    + Put audio and transcription files in subdirectory `clapi` of
      `<~/.speechrc:speech_arc>`.
    + Then run run the script `./import_trs.py clapi` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/clapi`.

- [ESLO-MD, Enquêtes Socio-Linguistiques à Orléans : Corpus Micro-Diachronie (French, 70 hours)](http://eslo.huma-num.fr/):
    + Download corpus from [ORTLOLANG](https://www.ortolang.fr/market/corpora/eslo-md)
      Three audio files are missing (ESLO1\_ENT\_141, ESLO2\_DIA\_1221 and ESLO2\_ENT\_1029),
      download them from the [main website](http://eslo.huma-num.fr/).
    + Move `.wav`/`.mp4` and `.trs` files in a subdirectory `elso-md` of `<~/.speechrc:speech_arc>`.
    + Then run run the script `./import_trs.py elso-md` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/elso-md`.

- [Forschergeist (German, 2 hours)](http://goofy.zamia.org/zamia-speech/corpora/forschergeist/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/forschergeist` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/forschergeist`

- [German Speechdata Package Version 2 (German, 148 hours)](http://www.repository.voxforge1.org/downloads/de/german-speechdata-package-v2.tar.gz):
    + Unpack the archive such that the directories `dev`, `test`, and `train` are
      direct subdirectories of `<~/.speechrc:speech_arc>/gspv2`. 
    + Then run run the script `./import_gspv2.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/gspv2`. 

- [Noise](http://goofy.zamia.org/zamia-speech/corpora/noise.tar.xz):
    + Download the tarball 
    + unpack it into the directory `<~/.speechrc:speech_corpora>/` (it will generate a `noise` subdirectory there)

- [LibriSpeech ASR (English, 475 hours)](http://www.openslr.org/12/):
    + Download the set of 360 hours "clean" speech tarball
    + Unpack the archive such that the directory `LibriSpeech` is a direct 
      subdirectory of `<~/.speechrc:speech_arc>`. 
    + Then run run the script `./import_librispeech.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/librispeech`. 

- [The LJ Speech Dataset (English, 24 hours)](https://keithito.com/LJ-Speech-Dataset/):
    + Download the tarball
    + Unpack the archive such that the directory `LJSpeech-1.1` is a direct 
      subdirectory of `<~/.speechrc:speech_arc>`. 
    + Then run run the script `import_ljspeech.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/lindajohnson-11`. 

- [Mozilla Common Voice French (French, 173 hours)](https://voice.mozilla.org/fr/datasets):
    + Download `fr.tar.gz`
    + Unpack the archive such that the directory `cv_fr` is a direct
      subdirectory of `<~/.speechrc:speech_arc>`.
    + Then run run the script `./import_mozfr.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/cv_fr`.

- [Mozilla Common Voice German (German, 140 hours)](https://voice.mozilla.org/en/datasets):
    + Download `de.tar.gz`
    + Unpack the archive such that the directory `cv_de` is a direct 
      subdirectory of `<~/.speechrc:speech_arc>`. 
    + Then run run the script `./import_mozde.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/cv_de`. 

- [Mozilla Common Voice V1 (English, 252 hours)](https://voice.mozilla.org/en/data):
    + Download `cv_corpus_v1.tar.gz`
    + Unpack the archive such that the directory `cv_corpus_v1` is a direct 
      subdirectory of `<~/.speechrc:speech_arc>`. 
    + Then run run the script `./import_mozcv1.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/cv_corpus_v1`. 

- [Munich Artificial Intelligence Laboratories GmbH (M-AILABS) Speech Dataset (English, 147 hours, German, 237 hours, French, 190 hours)](http://www.m-ailabs.bayern/en/):
    + Download `de_DE.tgz`, `en_UK.tgz`, `en_US.tgz`, `fr_FR.tgz` ([Mirror](https://www.caito.de/2019/01/the-m-ailabs-speech-dataset/))
    + Create a subdirectory `m_ailabs` in `<~/.speechrc:speech_arc>`
    + Unpack the downloaded tarbals inside the `m_ailabs` subdirectory
    + For French, create a directory `by_book` and move `male` and `female` directories in it as the archive does not follow exactly English and German structures
    + Then run run the script `./import_mailabs.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/m_ailabs_en`, `<~/.speechrc:speech_corpora>/m_ailabs_de` and `<~/.speechrc:speech_corpora>/m_ailabs_fr`.

- [TCOF, Traitement de Corpus Oraux en Français (French, 99 hours)](https://www.cnrtl.fr/corpus/tcof/):
    + Download corpus files (`.wav` and `.trs`).
    + Place all directories in a subdirectory `tcof` of `<~/.speechrc:speech_arc>`.
    + Then run run the script `./import_trs.py tcof` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/tcof`.

- [TED-LIUM Release 3 (English, 210 hours)](https://www.openslr.org/51/):
    + Download `TEDLIUM_release-3.tgz`
    + Unpack the archive such that the directory `TEDLIUM_release-3` is a direct 
      subdirectory of `<~/.speechrc:speech_arc>`. 
    + Then run run the script `./import_tedlium3.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/tedlium3`. 

- [VoxForge (English, 75 hours)](http://www.repository.voxforge1.org/downloads/SpeechCorpus/Trunk/Audio/Main/16kHz_16bit/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/voxforge_en` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/voxforge_en`

- [VoxForge (German, 56 hours)](http://www.repository.voxforge1.org/downloads/de/Trunk/Audio/Main/16kHz_16bit/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/voxforge_de` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/voxforge_de`

- [VoxForge (French, 140 hours)](http://www.repository.voxforge1.org/downloads/fr/Trunk/Audio/Main/16kHz_16bit/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/voxforge_fr` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/voxforge_fr`

- [Zamia (English, 5 minutes)](http://goofy.zamia.org/zamia-speech/corpora/zamia_en/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/zamia_en` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/zamia_en`

- [Zamia (German, 18 hours)](http://goofy.zamia.org/zamia-speech/corpora/zamia_de/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/zamia_de` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/zamia_de`


*Technical note*: For most corpora we have corrected transcripts in our databases which can be found
in `data/src/speech/<corpus_name>/transcripts_*.csv`. As these have been created by many hours of (semi-) 
manual review they should be of higher quality than the original prompts so they will be used during
training of our ASR models.

Once you have downloaded and, if necessary, converted a corpus you need to run

```bash
./speech_audio_scan.py <corpus name>
```

on it. This will add missing prompts to the CSV databases and convert audio files to 16kHz mono WAVE format.

*Technical note*: Please review new entries added by this script to CSV databases or revert the files to only
use entries we validated.

Adding Artificial Noise or Other Effects
----------------------------------------

To improve noise resistance it is possible to derive corpora from existing ones with noise added:

```bash
./speech_gen_noisy.py zamia_de
./speech_audio_scan.py zamia_de_noisy
cp data/src/speech/zamia_de/spk2gender data/src/speech/zamia_de_noisy/
cp data/src/speech/zamia_de/spk_test.txt data/src/speech/zamia_de_noisy/
./auto_review.py -a zamia_de_noisy
./apply_review.py -l de zamia_de_noisy review-result.csv 
```

This script will run recording through typical telephone codecs. Such a corpus can be used to train models
that support 8kHz phone recordings:

```bash
./speech_gen_phone.py zamia_de
./speech_audio_scan.py zamia_de_phone
cp data/src/speech/zamia_de/spk2gender data/src/speech/zamia_de_phone/
cp data/src/speech/zamia_de/spk_test.txt data/src/speech/zamia_de_phone/
./auto_review.py -a zamia_de_phone
./apply_review.py -l de zamia_de_phone review-result.csv 
```

Text Corpora
============

The following list contains text corpora that can be used to train language
models with the scripts contained in this repository:

- [Europarl](http://www.statmt.org/europarl/), specifically [parallel corpus German-English](http://www.statmt.org/europarl/v7/de-en.tgz) and [parallel corpus French-English](http://www.statmt.org/europarl/v7/fr-en.tgz): 
    + corresponding variable in `.speechrc`: `europarl_de`, `europarl_en`, `europarl_fr`
    + sentences extraction: run `./speech_sentences.py europarl_de`, `./speech_sentences.py europarl_en` and `./speech_sentences.py europarl_fr`

- [Cornell Movie--Dialogs Corpus](http://www.cs.cornell.edu/~cristian/Cornell_Movie-Dialogs_Corpus.html): 
    + corresponding variable in `.speechrc`: `cornell_movie_dialogs`
    + sentences extraction: run `./speech_sentences.py cornell_movie_dialogs`

- [German Parole Corpus](http://ota.ox.ac.uk/desc/2467): 
    + corresponding variable in `.speechrc`: `parole_de`
    + sentences extraction: train punkt tokenizer using `./speech_train_punkt_tokenizer.py`, then run `./speech_sentences.py parole_de`

- [WebQuestions](https://nlp.stanford.edu/software/sempre/): `web_questions`
    + corresponding variable in `.speechrc`: `web_questions`
    + sentences extraction: run `./speech_sentences.py web_questions`

- [Yahoo! Answers dataset](https://cogcomp.org/page/resource_view/89): `yahoo_answers`
    + corresponding variable in `.speechrc`: `yahoo_answers`
    + sentences extraction: run `./speech_sentences.py yahoo_answers`

- [CNRTL Est Républicain Corpus](http://cnrtl.fr/corpus/estrepublicain/), large corpus of news articles (4.3M headlines/paragraphs) available under a CC BY-NC-SA license. Download XML files and extract headlines and paragraphs to a text file with the following command: `xmllint --xpath '//*[local-name()="div"][@type="article"]//*[local-name()="p" or local-name()="head"]/text()' Annee*/*.xml | perl -pe 's/^  +//g ; s/^ (.+)/$1\n/g ; chomp' > est_republicain.txt`
    + corresponding variable in `.speechrc`: `est_republicain`
    + sentences extraction: run `./speech_sentences.py est_republicain`

Sentences can also be extracted from our speech corpora. To do that, run:

- English Speech Corpora
    + `./speech_sentences.py voxforge_en`
    + `./speech_sentences.py librispeech`
    + `./speech_sentences.py zamia_en`
    + `./speech_sentences.py cv_corpus_v1`
    + `./speech_sentences.py ljspeech`
    + `./speech_sentences.py m_ailabs_en`
    + `./speech_sentences.py tedlium3`

- German Speech Corpora
    + `./speech_sentences.py forschergeist`
    + `./speech_sentences.py gspv2`
    + `./speech_sentences.py voxforge_de`
    + `./speech_sentences.py zamia_de`
    + `./speech_sentences.py m_ailabs_de`
    + `./speech_sentences.py cv_de`

Language Model
==============

English
-------

Prerequisites: 
- text corpora `europarl_en`, `cornell_movie_dialogs`, `web_questions`, and `yahoo_answers` are installed, sentences extracted (see instructions above).
- sentences are extracted from speech corpora `librispeech`, `voxforge_en`, `zamia_en`, `cv_corpus_v1`, `ljspeech`, `m_ailabs_en`, `tedlium3`

To train a small, pruned English language model of order 4 using KenLM for use in both kaldi and wav2letter builds run:

```bash
./speech_build_lm.py generic_en_lang_model_small europarl_en cornell_movie_dialogs web_questions yahoo_answers librispeech voxforge_en zamia_en cv_corpus_v1 ljspeech m_ailabs_en tedlium3
```

to train a larger model of order 6 with less pruning:

```bash
./speech_build_lm.py -o 6 -p "0 0 0 0 1" generic_en_lang_model_large europarl_en cornell_movie_dialogs web_questions yahoo_answers librispeech voxforge_en zamia_en cv_corpus_v1 ljspeech m_ailabs_en tedlium3
```

to train a medium size model of order 5:

```bash
./speech_build_lm.py -o 5 -p "0 0 1 2" generic_en_lang_model_medium europarl_en cornell_movie_dialogs web_questions yahoo_answers librispeech voxforge_en zamia_en cv_corpus_v1 ljspeech m_ailabs_en tedlium3
```
German
------

Prerequisites: 
- text corpora `europarl_de` and `parole_de` are installed, sentences extracted (see instructions above).
- sentences are extracted from speech corpora `forschergeist`, `gspv2`, `voxforge_de`, `zamia_de`, `m_ailabs_de`, `cv_de`

To train a small, pruned German language model of order 4 using KenLM for use in both kaldi and wav2letter builds run:

```bash
./speech_build_lm.py generic_de_lang_model_small europarl_de parole_de forschergeist gspv2 voxforge_de zamia_de m_ailabs_de cv_de
```
to train a larger model of order 6 with less pruning:

```bash
./speech_build_lm.py -o 6 -p "0 0 0 0 1" generic_de_lang_model_large europarl_de parole_de forschergeist gspv2 voxforge_de zamia_de m_ailabs_de cv_de
```

to train a medium size model of order 5:

```bash
./speech_build_lm.py -o 5 -p "0 0 1 2" generic_de_lang_model_medium europarl_de parole_de forschergeist gspv2 voxforge_de zamia_de m_ailabs_de cv_de
```

French
------

Prerequisites:
- text corpora `europarl_fr` and `est_republicain` are installed, sentences extracted (see instructions above).
- sentences are extracted from speech corpora `voxforge_fr` and `m_ailabs_fr`

To train a French language model using KenLM run:
```bash
./speech_build_lm.py -k generic_fr_lang_model europarl_fr est_republicain voxforge_fr m_ailabs_fr
```

Submission Review and Transcription
===================================

The main tool used for submission review, transcription and lexicon expansion is:

```bash
./speech_editor.py
```


Lexica/Dictionaries
===================

*NOTE*: We use the terms lexicon and dictionary interchangably in this documentation and our scripts.

Currently, we have two lexica, one for English and one for German (in `data/src/dicts`):

- dict-en.ipa
    + English
    + originally based on The CMU Pronouncing Dictionary (http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
    + additional manual and Sequitur G2P based entries

- dict-de.ipa
    + started manually from scratch
    + once enough entries existed to train a reasonable Sequitur G2P model, many entries where converted from German wiktionary (see below)

The native format of our lexica is in (UTF8) IPA with semicolons as separator. This format is then converted to
whatever format is used by the target ASR engine by the corresponding export scripts.

Sequitur G2P
------------

Many lexicon-related tools rely on Sequitur G2P to compute pronunciations for words missing from the dictionary. The
necessary models can be downloaded from our file server: http://goofy.zamia.org/zamia-speech/g2p/ . 
For installation, download and unpack them and then put links to them under `data/models` like so:

```bash
data/models/sequitur-dict-de.ipa-latest -> <your model dir>/sequitur-dict-de.ipa-r20180510
data/models/sequitur-dict-en.ipa-latest -> <your model dir>/sequitur-dict-en.ipa-r20180510
```

To train your own Sequitur G2P models, use the export and train scripts provided, e.g.:

```bash
[guenter@dagobert speech]$ ./speech_sequitur_export.py -d dict-de.ipa
INFO:root:loading lexicon...
INFO:root:loading lexicon...done.
INFO:root:sequitur workdir data/dst/dict-models/dict-de.ipa/sequitur done.
[guenter@dagobert speech]$ ./speech_sequitur_train.sh dict-de.ipa
training sample: 322760 + 16988 devel
iteration: 0
...
```

Manual Editing
--------------

```bash
./speech_lex_edit.py word [word2 ...]
```

is the main curses based, interactive lexicon editor. It will automatically
produce candidate entries for new words using Sequitur G2P, MaryTTS and
eSpeakNG. The user can then edit these entries manually if necessary and check
them by listening to them being synthesized via MaryTTS in different voices.

The lexicon editor is also integrated into various other tools, `speech_editor.py` in particular
which allows you to transcribe, review and add missing words for new audio samples
within one tool - which is recommended.


I also tend to review lexicon entries randomly from time to time. For that I have a small script which will pick 20
random entries where Sequitur G2P disagrees with the current transcription in the lexicon:

```bash
./speech_lex_edit.py `./speech_lex_review.py`
```

Also, I sometimes use this command to add missing words from transcripts in batch mode:

```bash
./speech_lex_edit.py `./speech_lex_missing.py`
```

Wiktionary
----------

For the German lexicon, entries can be extracted from the German wiktionary using a set of scripts.
To do that, the first step is to extract a set of candidate entries from an wiktionary XML dump:

```bash
./wiktionary_extract_ipa.py 
```

this will output extracted entries to `data/dst/speech/de/dict_wiktionary_de.txt`. We now need to 
train a Sequitur G2P model that translates these entries into our own IPA style and phoneme set:

```bash
./wiktionary_sequitur_export.py
./wiktionary_sequitur_train.sh
```

finally, we translate the entries and check them against the predictions from our regular Sequitur G2P model:

```bash
./wiktionary_sequitur_gen.py
```

this script produces two output files: `data/dst/speech/de/dict_wiktionary_gen.txt` contains acceptable entries,
`data/dst/speech/de/dict_wiktionary_rej.txt` contains rejected entries.


Kaldi Models (recommended)
==========================

English NNet3 Chain Models
--------------------------

The following recipe trains Kaldi models for English. 

Before running it, make sure all prerequisites are met (see above for instructions on these):

- language model `generic_en_lang_model_small` built
- some or all speech corpora of `voxforge_en`, `librispeech`, `cv_corpus_v1`, `ljspeech`, `m_ailabs_en`, `tedlium3` and `zamia_en` are installed, converted and scanned.
- optionally noise augmented corpora: `voxforge_en_noisy`, `voxforge_en_phone`, `librispeech_en_noisy`, `librispeech_en_phone`, `cv_corpus_v1_noisy`, `cv_corpus_v1_phone`, `zamia_en_noisy` and `zamia_en_phone`

```bash
./speech_kaldi_export.py generic-en-small dict-en.ipa generic_en_lang_model_small voxforge_en librispeech zamia_en 
cd data/dst/asr-models/kaldi/generic-en-small
./run-chain.sh
```

export run with noise augmented corpora included:

```bash
./speech_kaldi_export.py generic-en dict-en.ipa generic_en_lang_model_small voxforge_en cv_corpus_v1 librispeech ljspeech m_ailabs_en tedlium3 zamia_en voxforge_en_noisy librispeech_noisy cv_corpus_v1_noisy cv_corpus_v1_phone zamia_en_noisy voxforge_en_phone librispeech_phone zamia_en_phone
```

German NNet3 Chain Models
-------------------------

The following recipe trains Kaldi models for German. 

Before running it, make sure all prerequisites are met (see above for instructions on these):

- language model `generic_de_lang_model_small` built
- some or all speech corpora of `voxforge_de`, `gspv2`, `forschergeist`, `zamia_de`, `m_ailabs_de`, `cv_de` are installed, converted and scanned.
- optionally noise augmented corpora: `voxforge_de_noisy`, `voxforge_de_phone`, `zamia_de_noisy` and `zamia_de_phone`

```bash
./speech_kaldi_export.py generic-de-small dict-de.ipa generic_de_lang_model_small voxforge_de gspv2 [ forschergeist zamia_de ...]
cd data/dst/asr-models/kaldi/generic-de-small
./run-chain.sh
```

export run with noise augmented corpora included:

```bash
./speech_kaldi_export.py generic-de dict-de.ipa generic_de_lang_model_small voxforge_de gspv2 forschergeist zamia_de voxforge_de_noisy voxforge_de_phone zamia_de_noisy zamia_de_phone m_ailabs_de cv_de
```

Model Adaptation
----------------

For a standalone kaldi model adaptation tool that does not require a complete zamia-speech setup, see

[kaldi-adapt-lm](https://github.com/gooofy/kaldi-adapt-lm)


Existing kaldi models (such as the ones we provide for download but also those you may train from scratch using our scripts)
can be adapted to (typically domain specific) language models, JSGF grammars and grammar FSTs.

Here is an example how to adapt our English model to a simple command and control JSGF grammar. Please note that this is just
a toy example - for real world usage you will probably want to add garbage phoneme loops to the grammar or produce a language
model that has some noise resistance built in right away. 

Here is the grammar we will use: 

```jsgf
#JSGF V1.0;

grammar org.zamia.control;

public <control> = <wake> | <politeCommand> ;

<wake> = ( good morning | hello | ok | activate ) computer;

<politeCommand> = [ please | kindly | could you ] <command> [ please | thanks | thank you ];

<command> = <onOffCommand> | <muteCommand> | <volumeCommand> | <weatherCommand>;

<onOffCommand> = [ turn | switch ] [the] ( light | fan | music | radio ) (on | off) ;

<volumeCommand> = turn ( up | down ) the ( volume | music | radio ) ;

<muteCommand> = mute the ( music | radio ) ;

<weatherCommand> = (what's | what) is the ( temperature | weather ) ;
```

the next step is to set up a kaldi model adaptation experiment using this script:

```bash
./speech_kaldi_adapt.py data/models/kaldi-generic-en-tdnn_250-latest dict-en.ipa control.jsgf control-en
```

here, `data/models/kaldi-generic-en-tdnn_250-latest` is the model to be adapted, `dict-en.ipa` is the dictionary which
will be used by the new model, `control.jsgf` is the JSGF grammar we want the model to be adapted to (you could specify an
FST source file or a language model instead here) and `control-en` is the name of the new model that will be created.

To run the actual adaptation, change into the model directory and run the adaptation script there:

```bash
cd data/dst/asr-models/kaldi/control-en
./run-adaptation.sh 
```

finally, you can create a tarball from the newly created model:

```bash
cd ../../../../..
./speech_dist.sh control-en kaldi adapt
```


wav2letter++ models
===================

English Wav2letter Models
-------------------------

```bash
./wav2letter_export.py -l en -v generic-en dict-en.ipa generic_en_lang_model_large voxforge_en cv_corpus_v1 librispeech ljspeech m_ailabs_en tedlium3 zamia_en voxforge_en_noisy librispeech_noisy cv_corpus_v1_noisy cv_corpus_v1_phone zamia_en_noisy voxforge_en_phone librispeech_phone zamia_en_phone
pushd data/dst/asr-models/wav2letter/generic-en/
bash run_train.sh
```

German Wav2letter Models
------------------------

```bash
./wav2letter_export.py -l de -v generic-de dict-de.ipa generic_de_lang_model_large voxforge_de gspv2 forschergeist zamia_de voxforge_de_noisy voxforge_de_phone zamia_de_noisy zamia_de_phone m_ailabs_de cv_de
pushd data/dst/asr-models/wav2letter/generic-de/
bash run_train.sh
```

auto-reviews using wav2letter
-----------------------------

create auto-review case:

```bash
./wav2letter_auto_review.py -l de w2l-generic-de-latest gspv2
```

run it:
```bash
pushd tmp/w2letter_auto_review
bash run_auto_review.sh
popd
```

apply the results:
```bash
./wav2letter_apply_review.py
```


Audiobook Segmentation and Transcription (Manual)
=================================================

Some notes on how to segment and transcribe audiobooks or other audio sources (e.g. from librivox) using
the abook scripts provided:

(0/3) Convert Audio to WAVE Format
----------------------------------

MP3
~~~
```bash
ffmpeg -i foo.mp3 foo.wav
```

MKV
~~~
```bash
mkvextract tracks foo.mkv 0:foo.ogg
opusdec foo.ogg foo.wav
```

(1/3) Convert Audio to 16kHz mono
---------------------------------

```bash
sox foo.wav -r 16000 -c 1 -b 16 foo_16m.wav
```


(2/3) Split Audio into Segments
-------------------------------

This tool will use silence detection to find good cut-points. You may want to adjust
its settings to achieve a good balance of short-segments but few words split in half.


```bash
./abook-segment.py foo_16m.wav
```

settings:

```bash
[guenter@dagobert speech]$ ./abook-segment.py -h
Usage: abook-segment.py [options] foo.wav

Options:
  -h, --help            show this help message and exit
  -s SILENCE_LEVEL, --silence-level=SILENCE_LEVEL
                        silence level (default: 2048 / 65536)
  -l MIN_SIL_LENGTH, --min-sil-length=MIN_SIL_LENGTH
                        minimum silence length (default:  0.07s)
  -m MIN_UTT_LENGTH, --min-utt-length=MIN_UTT_LENGTH
                        minimum utterance length (default:  2.00s)
  -M MAX_UTT_LENGTH, --max-utt-length=MAX_UTT_LENGTH
                        maximum utterance length (default:  9.00s)
  -o OUTDIRFN, --out-dir=OUTDIRFN
                        output directory (default: abook/segments)
  -v, --verbose         enable debug output
```

by default, the resulting segments will end up in abook/segments

(3/3) Transcribe Audio
----------------------

The transcription tool supports up to two speakers which you can specify on the command line.
The resulting voxforge-packages will end up in abook/out by default.


```bash
./abook-transcribe.py -s speaker1 -S speaker2 abook/segments/
```

Audiobook Segmentation and Transcription (kaldi)
================================================

Some notes on how to segment and transcribe semi-automatically audiobooks or other audio sources (e.g. from librivox) using
kaldi:

Directory Layout
----------------

Our scripts rely on a fixed directory layout. As segmentation of librivox recordings is one of the main
applications of these scripts, their terminology of books and sections is used here. For each section of 
a book two source files are needed: a wave file containing the audio and a text file containing the transcript.

A fixed naming scheme is used for those which is illustrated by this example:

<pre>
abook/in/librivox/11442-toten-Seelen/evak-11442-toten-Seelen-1.txt
abook/in/librivox/11442-toten-Seelen/evak-11442-toten-Seelen-1.wav
abook/in/librivox/11442-toten-Seelen/evak-11442-toten-Seelen-2.txt
abook/in/librivox/11442-toten-Seelen/evak-11442-toten-Seelen-2.wav
...
</pre>

The `abook-librivox.py` script is provided to help with retrieval of librivox recordings and setting up the
directory structure. Please note that for now, the tool will not retrieve transcripts automatically but
will create empty .txt files (according to the naming scheme) which you will have to fill in manually.

The tool will convert the retrieved audio to 16kHz mono wav format as required by the segmentation scripts, however.
If you intend to segment material from other sources, make sure to convert it to that format. For suggestions on
what tools to use for this step, please refer to the manual segmentation instructions in the previous section.

*NOTE*: As the kaldi process is parallelized for mass-segmentation, at least 4
audio and prompt files are needed for the process to work.

(1/4) Preprocess the Transcript
-------------------------------

This tool will tokenize the transcript and detect OOV tokens. Those can then be either
replaced or added to the dictionary:

```bash
./abook-preprocess-transcript.py abook/in/librivox/11442-toten-Seelen/evak-11442-toten-Seelen-1.txt
```

(2/4) Model adaptation
----------------------

For the automatic segmentation to work, we need a GMM model that is adapted to the current dictionary (which likely had
to be expanded during transcript preprocessing) plus uses a language model that covers the prompts.

First, we create a language model tuned for our purpose:

```bash
./abook-sentences.py abook/in/librivox/11442-toten-Seelen/*.prompt
./speech_build_lm.py abook_lang_model abook abook abook parole_de
```

Now we can create an adapted model using this language model and our current dict:

```bash
./speech_kaldi_adapt.py data/models/kaldi-generic-de-tri2b_chain-latest dict-de.ipa data/dst/lm/abook_lang_model/lm.arpa abook-de
pushd data/dst/asr-models/kaldi/abook-de
./run-adaptation.sh
popd
./speech_dist.sh -c abook-de kaldi adapt
tar xfvJ data/dist/asr-models/kaldi-abook-de-adapt-current.tar.xz -C data/models/
```

(3/4) Auto-Segment using Kaldi
------------------------------

Next, we need to create the kaldi directory structure and files for auto-segmentation:

```bash
./abook-kaldi-segment.py data/models/kaldi-abook-de-adapt-current abook/in/librivox/11442-toten-Seelen
```

now we can run the segmentation:

```bash
pushd data/dst/speech/asr-models/kaldi/segmentation
./run-segmentation.sh 
popd
```

(4/4) Retrieve Segmentation Result
----------------------------------

Finally, we can retrieve the segmentation result in voxforge format:

```bash
./abook-kaldi-retrieve.py abook/in/librivox/11442-toten-Seelen/
```

Training Voices for Zamia-TTS
=============================

Zamia-TTS is an experimental project that tries to train TTS voices based on (reviewed) Zamia-Speech data. Downloads here:

https://goofy.zamia.org/zamia-speech/tts/

Tacotron 2
----------

This section describes how to train voices for [NVIDIA's Tacotron 2 implementation](https://github.com/NVIDIA/tacotron2). 
The resulting voices will have a sample rate of 16kHz as that is the default
sample rate used for Zamia Speech ASR model training. This means that you will have to use a 16kHz waveglow model which you can find, along with pretrained voices and sample wavs here:

https://goofy.zamia.org/zamia-speech/tts/tacotron2/

now with that out of the way, Tacotron 2 model training is pretty straightforward. First step is to export filelists for the voice you'd like to train, e.g.:

```bash
./speech_tacotron2_export.py -l en -o ../torch/tacotron2/filelists m_ailabs_en mailabselliotmiller
```
next, change into your Tacotron 2 training directory

```bash
cd ../torch/tacotron2
```

and specify file lists, sampling rate and batch size in ''hparams.py'':

```
diff --git a/hparams.py b/hparams.py
index 8886f18..75e89c9 100644
--- a/hparams.py
+++ b/hparams.py
@@ -25,15 +25,19 @@ def create_hparams(hparams_string=None, verbose=False):
         # Data Parameters             #
         ################################
         load_mel_from_disk=False,
-        training_files='filelists/ljs_audio_text_train_filelist.txt',
-        validation_files='filelists/ljs_audio_text_val_filelist.txt',
-        text_cleaners=['english_cleaners'],
+        training_files='filelists/mailabselliotmiller_train_filelist.txt',
+        validation_files='filelists/mailabselliotmiller_val_filelist.txt',
+        text_cleaners=['basic_cleaners'],
 
         ################################
         # Audio Parameters             #
         ################################
         max_wav_value=32768.0,
-        sampling_rate=22050,
+        #sampling_rate=22050,
+        sampling_rate=16000,
         filter_length=1024,
         hop_length=256,
         win_length=1024,
@@ -81,7 +85,8 @@ def create_hparams(hparams_string=None, verbose=False):
         learning_rate=1e-3,
         weight_decay=1e-6,
         grad_clip_thresh=1.0,
-        batch_size=64,
+        # batch_size=64,
+        batch_size=16,
         mask_padding=True  # set model's padded outputs to padded values
     )
```

and start the training:

```bash
python train.py --output_directory=elliot --log_directory=elliot/logs
```

Tacotron
--------

* (1/2) Prepare a training data set

```bash
./ztts_prepare.py -l en m_ailabs_en mailabselliotmiller elliot
```

* (2/2) Run the training

```bash
./ztts_train.py -v elliot 2>&1 | tee train_elliot.log
```

Model Distribution
==================

To build tarballs from models, use the `speech-dist.sh` script, e.g.:


```bash
./speech_dist.sh generic-en kaldi tdnn_sp

```

License
=======

My own scripts as well as the data I create (i.e. lexicon and transcripts) is
LGPLv3 licensed unless otherwise noted in the script's copyright headers.

Some scripts and files are based on works of others, in those cases it is my
intention to keep the original license intact. Please make sure to check the
copyright headers inside for more information.

Authors
=======

* Guenter Bartsch <guenter@zamia.org>
* Marc Puels <marc@zamia.org>
* Paul Guyot <pguyot@kallisys.net>

