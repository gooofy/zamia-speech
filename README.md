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

speech_corpora        = /home/bofh/projects/ai/data/speech_corpora

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

Speech Corpora
==============

The following list contains speech corpora supported by this script collection.

- [Forschergeist (German)](http://goofy.zamia.org/voxforge/de/audio/forschergeist/):
  Download all tar.xz files into the directory
  `<~/.speechrc:audio_corpora>/zamia_de` and unpack them.

- [German Speechdata Package Version 2](http://www.repository.voxforge1.org/downloads/de/german-speechdata-package-v2.tar.gz):
  Unpack the archive such that the directories `dev`, `test`, and `train` are
  direct subdirectories of `<~/.speechrc:audio_corpora>/gspv2_orig`. Then run
  run the script `./gspv2_to_vf.py` to convert the corpus to the VoxForge
  format. The resulting corpus will be written to
  `<~/.speechrc:speech_corpora>/gspv2`. You can find corrected prompts in
  `data/src/speech/gspv2/transcripts_*.csv`. These prompts are used during
  training of ASR models.

- [VoxForge (German)](http://www.repository.voxforge1.org/downloads/de/Trunk/Audio/Main/16kHz_16bit/):
  Put the tar.gz archives into the directory
  `<~/.speechrc:speech_corpora>/voxforge_de` and unpack them. You can find
  manually corrected prompts in `data/src/speech/voxforge_de/transcripts_*.csv`.
  These prompts are used during training of ASR models.

- [Zamia (German)](http://goofy.zamia.org/voxforge/de/audio/zamia_de/):
  Download all tar.xz files into the directory
  `<~/.speechrc:audio_corpora>/zamia_de` and unpack them.

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

extract sentences from corpora:

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

gspv2
=====

To train an ASR system based on these scripts the German Speechdata Package
Version 2 has to be transformed into the VoxForge format with

```bash
./gspv2_to_vf.py
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

Wiktionary
----------

For the german lexicon, entries can be extracted from the german wiktionary using a set of scripts.
To do that, the first step is to extract a set of candidate entries from an wiktionary XML dump:

```bash
./wiktionary_extract_ipa.py 
```

this will output extracted entries to `data/dst/speech/de/dict_wiktionary_de.txt`. We now need to 
train a sequitur model that translates these entries into our own IPA style and phoneme set:

```bash
./wiktionary_sequitur_export.py
./wiktionary_sequitur_train.sh
```

finally, we translate the entries and check them against the predictions from our regular sequitur model:

```bash
./wiktionary_sequitur_gen.py
```

this script produces two output files: `data/dst/speech/de/dict_wiktionary_gen.txt` contains acceptable entries,
`data/dst/speech/de/dict_wiktionary_rej.txt` contains rejected entries.


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

The following example trains a Kaldi model for German. Before running it, make
sure to have downloaded the text corpora Europarl and Parole. Furthermore, you
need the German VoxForge corpus and the gspv2 corpus. Unpack the German VoxForge
corpus under `<~/.speechrc:speech_corpora>/voxforge_de/` and the gspv2 corpus
under `<~/.speechrc:speech_corpora>/gspv2_orig/`.

```bash
./speech_sentences.py europarl-de
./speech_train_punkt_tokenizer.py  # Required for ./speech_sentences.py parole
./speech_sentences.py parole
./speech_build_lm.py my_lang_model europarl-de parole
./gspv2_to_vf.py
./speech_audio_scan.py voxforge_de gspv2
./speech_kaldi_export.py my_asr_model dict-de.ipa my_lang_model voxforge_de gspv2
cd data/dst/asr-models/my_asr_model
./run-lm.sh
./run-chain.sh
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

