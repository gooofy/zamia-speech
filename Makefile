SHELL := /bin/bash

all:	prolog 

prolog:
	./nlp_cli.py compile common_sense weather smalltalk radio

kb:
	./nlp_cli.py kb_import all

cron:
	./nlp_cli.py cron all

train:
	./nlp_cli.py train

kaldi:
	rm -rf data/dst/speech/de/kaldi
	./speech_kaldi_export.py
	pushd data/dst/speech/de/kaldi && ./run.sh && popd

sphinx:
	rm -rf data/dst/speech/de/cmusphinx
	./speech_sphinx_export.py 
	pushd data/dst/speech/de/cmusphinx && ./sphinx-run.sh && popd
	
sequitur:
	rm -rf data/dst/speech/de/sequitur/
	./speech_sequitur_export.py
	./speech_sequitur_train.sh

stats:
	./speech_stats.py

clean:
	./nlp_cli.py clean -a all
	# rm -rf data/dst/*
