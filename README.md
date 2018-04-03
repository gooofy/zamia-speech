# Speech

Python scripts to compute audio and language models from voxforge.org speech data.
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

Links
=====

* [Data / Models](http://goofy.zamia.org/voxforge/ "models")

* [Code](https://github.com/gooofy/nlp "github")

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

vf_audiodir_de        = /home/bofh/projects/ai/data/speech/de/voxforge/audio
vf_contribdir_de      = /home/bofh/projects/ai/data/speech/de/voxforge/audio-contrib
extrasdir_de          = /home/bofh/projects/ai/data/speech/de/kitchen
gspv2_dir             = /home/bofh/projects/ai/data/speech/de/gspv2

vf_audiodir_en        = /home/bofh/projects/ai/data/speech/en/voxforge/audio
extrasdir_en          = /home/bofh/projects/ai/data/speech/en/kitchen
librivoxdir           = /home/bofh/projects/ai/data/speech/en/lsvf

kaldi_root            = /apps/kaldi-cuda
srilm_root            = /apps/kaldi-cuda/tools/srilm

wav16_dir_de          = /home/bofh/projects/ai/data/speech/de/16kHz
wav16_dir_en          = /home/bofh/projects/ai/data/speech/en/16kHz
noise_dir             = /home/bofh/projects/ai/data/speech/noise

europarl_de           = /home/bofh/projects/ai/data/corpora/de/europarl-v7.de-en.de
parole_de             = /home/bofh/projects/ai/data/corpora/de/German Parole Corpus/DE_Parole/

europarl_en           = /home/bofh/projects/ai/data/corpora/en/europarl-v7.de-en.en
cornell_movie_dialogs = /home/bofh/projects/ai/data/corpora/en/cornell_movie_dialogs_corpus
web_questions         = /home/bofh/projects/ai/data/corpora/en/WebQuestions
yahoo_answers         = /home/bofh/projects/ai/data/corpora/en/YahooAnswers

host_asr              = localhost
port_asr              = 8301

kaldi_model_dir_de    = /home/bofh/projects/ai/speech/data/models/kaldi-nnet3-voxforge-de-latest
kaldi_model_de        = nnet_tdnn_a

host_getty            = localhost
port_getty            = 8298
port_gettyp           = 8299

[tts]
host                  = localhost
port                  = 8300
```

Links to Text Corpora
=====================

The following list contains text corpora that can be used to train language
models with the scripts contained in this repository. Right of the name of the
corpus is the corresponding variable in `.speechrc`.

- [Europarl](http://www.statmt.org/europarl/), specifically [parallel corpus German-English](http://www.statmt.org/europarl/v7/de-en.tgz): `europarl_de`, `europarl_en`
- [Cornell Movie--Dialogs Corpus](http://www.cs.cornell.edu/~cristian/Cornell_Movie-Dialogs_Corpus.html): `cornell_movie_dialogs`
- [German Parole Corpus](http://ota.ox.ac.uk/desc/2467): `parole_de`
- [WebQuestions](https://nlp.stanford.edu/software/sempre/): `web_questions`
- [Yahoo! Answers dataset](https://cogcomp.org/page/resource_view/89): `yahoo_answers`


Language Model
==============

extract sentences from corpuses:

```bash
./speech_sentences.py
```

train language model using SRILM for use in both sphinx and kaldi builds:

```bash
./speech_build_lm.py
```

voxforge
========

download latest audio data from voxforge, add them to submissions:

```bash
./speech_pull_voxforge.sh
./speech_audio_scan.py
```

Submission Review and Transcription
===================================

The main tool used for submission review, transcription and lexicon expansion is:

```bash
./speech_editor.py
```


Lexicon
=======

The lexicon used here (data/src/speech/de/dict.ipa) is my own creation, i.e. entries have been manually checked and
added using my `speech_editor` / `lex_editor` tools. For new entries, I usually let MaryTTS, espeak and sequitur generate
phonemes, listen to them using MaryTTS and pick the best one. Quite frequently I will still make manual adjustments
(typically I will add or move stress markers, syllable boundaries, change vocal lengths, ...), often using additional
sources like wiktionary which has IPA transcriptions for many words.

In general it is recommended to use the `speech_editor.py` tool (see above) which ensures all lexicon entries
are actually covered by audio submissions. However, there are tools which work on the lexicon directly:

I also tend to review lexicon entries randomly from time to time. For that I have a small script which will pick 20
random entries where sequitur disagrees with the current transcription in the lexicon:

```bash
./speech_lex_edit.py `./speech_lex_review.py`
```

Also, I sometimes use this command to add missing words from transcripts in batch mode:

```bash
./speech_lex_edit.py `./speech_lex_missing.py`
```

CMU Sphinx Model
================

To build the CMU Sphinx continous model:

```bash
./speech_sphinx_export.py
cd data/dst/speech/de/cmusphinx_cont/
./sphinx-run.sh
```

Running pocketsphinx
--------------------

just a sample invocation for live audio from mic:

    pocketsphinx_continuous \
        -hmm model_parameters/voxforge.cd_cont_6000 \
        -lw 10 -feat 1s_c_d_dd -beam 1e-80 -wbeam 1e-40 \
        -dict etc/voxforge.dic \
        -lm etc/voxforge.lm.bin \
        -wip 0.2 \
        -agc none -varnorm no -cmn current

Kaldi Models
============

NNet3 Models
------------

To build the kaldi models:

```bash
./speech_kaldi_export.py
cd data/dst/speech/de/kaldi/
./run-lm.sh
./run-chain.sh
```

Audiobook Segmentation and Transcription
========================================

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

