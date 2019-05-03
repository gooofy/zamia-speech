SHELL := /bin/bash

all:	stats

kaldi:
	rm -rf data/dst/speech/de/kaldi
	./speech_kaldi_export.py
	pushd data/dst/speech/de/kaldi && ./run.sh && popd

sequitur:
	rm -rf data/dst/speech/de/sequitur/
	./speech_sequitur_export.py
	./speech_sequitur_train.sh

stats:
	./speech_stats.py

clean:
	# rm -rf data/dst/*

