# Zamia Speech

Python scripts to compute audio and language models from voxforge.org speech data and many sources.
Models that can be built include:

* CMU Sphinx continous and PTM audio models
* Kaldi nnet3 chain audio models
* srilm language model
* sequitur g2p model

*Important*: Please note that these scripts form in no way a complete application ready for end-user consumption.
However, if you are a developer interested in natural language processing you may find some of them useful.
Contributions, patches and pull requests are very welcome.

At the time of this writing, the scripts here are focused on building the english and german VoxForge models. 
However, there is no reason why they couldn't be used to build other language models as well, feel free to 
contribute support for those.


Table of Contents
=================

* [Zamia Speech](#zamia-speech)
* [Links](#links)
* [Requirements](#requirements)
* [Setup Notes](#setup-notes)
* [Speech Corpora](#speech-corpora)
  * [Adding Artificial Noise or Other Effects](#adding-artificial-noise-or-other-effects)
* [Text Corpora](#text-corpora)
* [Language Model](#language-model)
  * [German](#german)
* [Submission Review and Transcription](#submission-review-and-transcription)
* [Lexica/Dictionaries](#lexicadictionaries)
  * [Sequitur G2P](#sequitur-g2p)
  * [Manual Editing](#manual-editing)
  * [Wiktionary](#wiktionary)
* [Kaldi Models (recommended)](#kaldi-models-recommended)
  * [NNet3 Chain Models](#nnet3-chain-models)
* [CMU Sphinx Models](#cmu-sphinx-models)
  * [Running pocketsphinx](#running-pocketsphinx)
* [Audiobook Segmentation and Transcription (Manual)](#audiobook-segmentation-and-transcription-manual)
  * [(0/3) Convert Audio to WAVE Format](#03-convert-audio-to-wave-format)
  * [(1/3) Convert Audio to 16kHz mono](#13-convert-audio-to-16khz-mono)
  * [(2/3) Split Audio into Segments](#23-split-audio-into-segments)
  * [(3/3) Transcribe Audio](#33-transcribe-audio)
* [Audiobook Segmentation and Transcription (kaldi)](#audiobook-segmentation-and-transcription-kaldi)
  * [(0/4) Convert Audio to WAVE Format](#04-convert-audio-to-wave-format)
  * [(1/4) Convert Audio to 16kHz mono](#14-convert-audio-to-16khz-mono)
  * [(2/4) Preprocess the Transcript](#24-preprocess-the-transcript)
  * [(3/4) Auto\-Segment using Kaldi](#34-auto-segment-using-kaldi)
  * [(4/4) Retrieve Segmentation Result](#44-retrieve-segmentation-result)
* [License](#license)
* [Author](#author)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc.go)


Links
=====

* [Data / Models](http://goofy.zamia.org/voxforge/ "models")

* [Code](https://github.com/gooofy/nlp "github")

Get Started with our Pre-Trained Models 
=======================================

Raspbian on Raspberry Pi 3
--------------------------

### (1/3) setup apt-source and install packages

```bash
pi@raspberrypi:~ $ sudo -i

root@raspberrypi:~# echo "deb http://goofy.zamia.org/raspbian-ai/ ./"
>/etc/apt/sources.list.d/zamia-ai.list
root@raspberrypi:~# wget -qO -
http://goofy.zamia.org/raspbian-ai/bofh.asc | sudo apt-key add -
root@raspberrypi:~# apt-get update
root@raspberrypi:~# apt-get install kaldi-chain-voxforge-de
kaldi-chain-voxforge-en python-kaldiasr python-nltools
pulseaudio-utils pulseaudio
root@raspberrypi:~# exit
```

### (2/3) determine the name of your pulseaudio mic source

```bash
pi@raspberrypi:~ $ pactl list sources
Source #0
    State: SUSPENDED
    Name: alsa_input.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-mono
    Description: CM108 Audio Controller Analog Mono
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

### (3/3) download and run demo

```bash
pi@raspberrypi:~ $ wget
'https://raw.githubusercontent.com/gooofy/py-kaldi-asr/master/examples/chain_live.py'

pi@raspberrypi:~ $ python chain_live.py -s 'CM108'
Kaldi live demo V0.1
Loading model from /opt/kaldi/model/kaldi-chain-voxforge-de ...
Please speak.
hallo computer
schalte bitte das radio ein
mach bitte das licht an
wie wird das wetter in stuttgart
wie geht es dir
vielen dank
auf wiedersehen
```


Requirements
============

*Note*: probably incomplete.

* Python 2.7 with nltk, numpy, ...
* CMU Sphinx
* srilm
* kaldi
* py-nltools
* sox

To set up a Conda environment named `gooofy-speech` with all Python
dependencies installed, run

    $ conda env create -f environment.yml

To activate the environment, run

    $ source activate gooofy-speech

To deactivate the environment, run

    $ source deactivate

*Note*: The Conda environment was created on a Linux machine, so maybe it won't
work on other machines.

While the environment is activated, you may want to install additional packages
with `conda install` or `pip install`. After doing so, update `environment.yml`
with

    $ ./update_conda_env.sh

Afterwards you can commit the changes to the repository.

Setup Notes
===========

Just some rough notes on the environment needed to get these scripts to run. This is in no way a complete set of
instructions, just some hints to get you started.

`~/.speechrc`:

```ini
[speech]
vf_login              = <your voxforge login>

speech_arc            = /home/bofh/projects/ai/data/speech/arc
speech_corpora        = /home/bofh/projects/ai/data/speech/corpora

kaldi_root            = /apps/kaldi-cuda
srilm_root            = /apps/kaldi-cuda/tools/srilm

wav16                 = /home/bofh/projects/ai/data/speech/16kHz
noise_dir             = /home/bofh/projects/ai/data/speech/noise

europarl_de           = /home/bofh/projects/ai/data/corpora/de/europarl-v7.de-en.de
parole_de             = /home/bofh/projects/ai/data/corpora/de/German Parole Corpus/DE_Parole/

europarl_en           = /home/bofh/projects/ai/data/corpora/en/europarl-v7.de-en.en
cornell_movie_dialogs = /home/bofh/projects/ai/data/corpora/en/cornell_movie_dialogs_corpus
web_questions         = /home/bofh/projects/ai/data/corpora/en/WebQuestions
yahoo_answers         = /home/bofh/projects/ai/data/corpora/en/YahooAnswers

wiktionary_de         = /home/bofh/projects/ai/data/corpora/de/dewiktionary-20180320-pages-meta-current.xml

[tts]
host                  = localhost
port                  = 8300
```

Speech Corpora
==============

The following list contains speech corpora supported by this script collection.

- [Forschergeist (German)](http://goofy.zamia.org/voxforge/de/audio/forschergeist/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/forschergeist` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/forschergeist`

- [German Speechdata Package Version 2](http://www.repository.voxforge1.org/downloads/de/german-speechdata-package-v2.tar.gz):
    + Unpack the archive such that the directories `dev`, `test`, and `train` are
      direct subdirectories of `<~/.speechrc:speech_arc>/gspv2`. 
    + Then run run the script `./gspv2_to_vf.py` to convert the corpus to the VoxForge
      format. The resulting corpus will be written to `<~/.speechrc:speech_corpora>/gspv2`. 

- [Noise](http://goofy.zamia.org/voxforge/):
    + Download the tarball 
    + unpack it into the directory `<~/.speechrc:speech_corpora>/` (it will generate a `noise` subdirectory there)

- [VoxForge (English)](http://www.repository.voxforge1.org/downloads/SpeechCorpus/Trunk/Audio/Main/16kHz_16bit/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/voxforge_en` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/voxforge_en`

- [VoxForge (German)](http://www.repository.voxforge1.org/downloads/de/Trunk/Audio/Main/16kHz_16bit/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/voxforge_de` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/voxforge_de`

- [Zamia (German)](http://goofy.zamia.org/voxforge/de/audio/zamia_de/):
    + Download all .tgz files into the directory `<~/.speechrc:speech_arc>/zamia_de` 
    + unpack them into the directory `<~/.speechrc:speech_corpora>/zamia_de`


*Technical note*: For most corpora we have corrected transcripts in our databases which can be found
in `data/src/speech/<corpus_name>/transcripts_*.csv`. As these have been created by many hours of (semi-) 
manual review they should be of higher quality than the original prompts so they will be used during
training of our ASR models.

Once you have downloaded and, if necessary, converted a corpus you need to run

```bash
./speech_audio_scan <corpus name>
```

on it. This will add missing prompts to the CSV databases and convert audio files to 16kHz mono WAVE format.

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

- [Europarl](http://www.statmt.org/europarl/), specifically [parallel corpus German-English](http://www.statmt.org/europarl/v7/de-en.tgz): 
    + corresponding variable in `.speechrc`: `europarl_de`, `europarl_en`
    + sentences extraction: run `./speech_sentences.py europarl_de` and `./speech_sentences.py europarl_en`

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

Sentences can also be extracted from our speech corpora. To do that, run:

- English Speech Corpora
    + `./speech_sentences.py voxforge_en`
    + `./speech_sentences.py librispeech`

- German Speech Corpora
    + `./speech_sentences.py forschergeist`
    + `./speech_sentences.py gspv2`
    + `./speech_sentences.py voxforge_de`
    + `./speech_sentences.py zamia_de`

Language Model
==============

German
------

Prerequisites: 
- text corpora `europarl_de` and `parole_de` are installed, sentences extracted (see instructions above).
- sententences are extracted from speech corpora `forschergeist`, `gspv2`, `voxforge_de`, `zamia_de`

To train a german language model using SRILM for use in both sphinx and kaldi builds run:

```bash
./speech_build_lm.py generic_de_lang_model europarl_de parole_de forschergeist gspv2 voxforge_de zamia_de
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

Currently, we have two lexica, one for english and one for german (in `data/src/dicts`):

- dict-en.ipa
    + english
    + originally based on The CMU Pronouncing Dictionary (http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
    + additional manual and Sequitur G2P based entries

- dict-de.ipa
    + started manually from scratch
    + once enough entries existed to train a reasonable Sequitur G2P model, many entries where converted from german wiktionary (see below)

The native format of our lexica is in (UTF8) IPA with semicolons as separator. This format is then converted to
whatever format is used by the target ASR engine by the corresponding export scripts.

Sequitur G2P
------------

Many lexicon-related tools rely on Sequitur G2P to compute pronounciations for words missing from the dictionary. The
necessary models can be downloaded from our file server: [english](http://goofy.zamia.org/voxforge/en/) and 
[german](http://goofy.zamia.org/voxforge/de/). Fpr installation download and unpack them and then put links to them
under `data/models` like so:

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
produce candidate entries for new new words using Sequitur G2P, MaryTTS and
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

For the german lexicon, entries can be extracted from the german wiktionary using a set of scripts.
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

NNet3 Chain Models
------------------

The following recipe trains a Kaldi model for German. 

Before running it, make sure all prerequisites are met (see above for instructions on these):

- language model `generic_de_lang_model` built
- some or all speech corpora of `voxforge_de`, `gspv2`, `forschergeist` and `zamia_de` are installed, converted and scanned.
- optionally noise augmented corpora: `voxforge_de_noisy`, `voxforge_de_phone`, `zamia_de_noisy` and `zamia_de_phone`

```bash
./speech_kaldi_export.py generic-de dict-de.ipa generic_de_lang_model voxforge_de gspv2 [ forschergeist zamia_de ...]
cd data/dst/asr-models/kaldi/generic-de
./run-lm.sh
./run-chain.sh
```

complete export run with noise augmented corpora included:

```bash
./speech_kaldi_export.py generic-de2 dict-de.ipa generic_de_lang_model voxforge_de gspv2 forschergeist zamia_de voxforge_de_noisy voxforge_de_phone zamia_de_noisy zamia_de_phone
```

CMU Sphinx Models
=================

The following recipe trains a continous CMU Sphinx model for German. 

Before running it, make sure all prerequisites are met (see above for instructions on these):

- language model `generic_de_lang_model` built
- some or all speech corpora of `voxforge_de`, `gspv2`, `forschergeist` and `zamia_de` are installed, converted and scanned.
- optionally noise augmented corpora: `voxforge_de_noisy`, `voxforge_de_phone`, `zamia_de_noisy` and `zamia_de_phone`

```bash
./speech_sphinx_export.py generic-de dict-de.ipa generic_de_lang_model voxforge_de gspv2 [ forschergeist zamia_de ...]
cd data/dst/asr-models/cmusphinx_cont/generic-de
./sphinx-run.sh
```

complete export run with noise augmented corpora included:

```bash
./speech_sphinx_export.py generic-de2 dict-de.ipa generic_de_lang_model voxforge_de gspv2 forschergeist zamia_de voxforge_de_noisy voxforge_de_phone zamia_de_noisy zamia_de_phone
```

for resource constrained applications PTM models can be trained:

```bash
./speech_sphinx_export.py generic-de dict-de.ipa generic_de_lang_model voxforge_de gspv2 [ forschergeist zamia_de ...]
cd data/dst/asr-models/cmusphinx_ptm/generic-de
./sphinx-run.sh
```


Running pocketsphinx
--------------------

*IMPORTANT*: In order to use our pre-built models you have to use up-to-date CMU Sphinx. Unfortunately, at the time
             of this writing even the latest "5prealpha" release is outdated. Until the CMU Sphinx project has a new release,
             we highly recommend to check out and build it yourself from their github repository.

Here are some sample invocations for pocketsphinx which should help get you started using our models:

```bash
pocketsphinx_continuous -lw 10 -fwdflatlw 10 -bestpathlw 10 -beam 1e-80 \
                        -wbeam 1e-40 -fwdflatbeam 1e-80 -fwdflatwbeam 1e-40 \
                        -pbeam 1e-80 -lpbeam 1e-80 -lponlybeam 1e-80 \
                        -wip 0.2 -agc none -varnorm no -cmn current \
                        -lowerf 130 -upperf 6800 -nfilt  25 \
                        -transform dct -lifter 22 -ncep   13 \
                        -hmm ${MODELDIR}/model_parameters/voxforge.cd_cont_6000 \
                        -dict ${MODELDIR}/etc/voxforge.dic \
                        -lm ${MODELDIR}/etc/voxforge.lm.bin \
                        -infile $WAVFILE 


sphinx_fe -c fileids -di wav -do mfcc \
          -part 1 -npart 1 -ei wav -eo mfc -nist no -raw no -mswav yes \
          -samprate 16000 -lowerf 130 -upperf 6800 -nfilt 25 -transform dct -lifter 22

pocketsphinx_batch -hmm ${MODELDIR}/model_parameters/voxforge.cd_cont_6000 \
                   -feat 1s_c_d_dd \
                   -ceplen 13 \
                   -ncep 13 \
                   -lw 10 \
                   -fwdflatlw 10 \
                   -bestpathlw 10 \
                   -beam 1e-80 \
                   -wbeam 1e-40 \
                   -fwdflatbeam 1e-80 \
                   -fwdflatwbeam 1e-40 \
                   -pbeam 1e-80 \
                   -lpbeam 1e-80 \
                   -lponlybeam 1e-80 \
                   -dict ${MODELDIR}/etc/voxforge.dic \
                   -wip 0.2 \
                   -ctl fileids \
                   -cepdir ./mfcc \
                   -cepext .mfc \
                   -hyp test_batch.match \
                   -logfn test_batch.log \
                   -agc none -varnorm no -cmn current -lm ${MODELDIR}/etc/voxforge.lm.bin
```

You can download a complete tarball with example scripts and WAV files here:

http://goofy.zamia.org/voxforge/sphinx-example.tgz

*NOTE*: According to https://github.com/cmusphinx/pocketsphinx/issues/116 
        pocketsphinx\_continuous will have worse results compared to pocketsphinx\_batch using the same model and parameters.


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
sox foo.wav -r 16000 -c 1 foo\_16m.wav
```


(2/3) Split Audio into Segments
-------------------------------

This tool will use silence detection to find good cut-points. You may want to adjust
its settings to achieve a good balance of short-segments but few words split in half.


```bash
./abook-segment.py foo\_16m.wav
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

(0/4) Convert Audio to WAVE Format
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

(1/4) Convert Audio to 16kHz mono
---------------------------------

```bash
sox foo.wav -r 16000 -c 1 foo\_16m.wav
```

(2/4) Preprocess the Transcript
-------------------------------

This tool will tokenize the transcript and detect OOV tokens. Those can then be either
replaced or added to the dictionary:

```bash
./abook-preprocess-transcript.py abook/in/librivox/sammlung-kurzer-deutscher-prosa-022/dirkweber-sammlung-kurzer-deutscher-prosa-022-03.txt
mv prompts.txt abook/in/librivox/sammlung-kurzer-deutscher-prosa-022/dirkweber-sammlung-kurzer-deutscher-prosa-022-03.prompt
```

make sure to put all wav and prompt files into the same directory. As the kaldi process is parallelized for mass-segmentation, 
at least 4 audio and prompt files are needed for the process to work.

(3/4) Auto-Segment using Kaldi
------------------------------

Next, we need to create the kaldi directory structure and files for processing:

```bash
./abook-kaldi-segment.py abook/in/librivox/sammlung-kurzer-deutscher-prosa-022/
```

now we can run the segmentation:

```bash
pushd data/dst/speech/de/kaldi/
./run-segmentation.sh 
popd
```

(4/4) Retrieve Segmentation Result
----------------------------------

Finally, we can retrieve the segmentation result in voxforge format:

```bash
./abook-kaldi-retrieve.py abook/in/librivox/sammlung-kurzer-deutscher-prosa-022/
```


License
=======

My own scripts as well as the data I create (i.e. lexicon and transcripts) is
LGPLv3 licensed unless otherwise noted in the script's copyright headers.

Some scripts and files are based on works of others, in those cases it is my
intention to keep the original license intact. Please make sure to check the
copyright headers inside for more information.

Author
======

Guenter Bartsch <guenter@zamia.org>
Conda environment and many bugfixes contributed by mpuels (https://github.com/mpuels)

