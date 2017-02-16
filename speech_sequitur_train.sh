#!/bin/bash

SEQUITUR_ROOT=/apps/sequitur
WORKDIR=data/dst/speech/de/sequitur

export PYTHONPATH="$SEQUITUR_ROOT/lib64/python2.7/site-packages/:$PYTHONPATH"
export PATH="$SEQUITUR_ROOT/bin:$PATH"

cd $WORKDIR

g2p.py --train train.lex --devel 5% --write-model model-1
g2p.py --model model-1 --test test.lex > model-1.test
g2p.py --model model-1 --ramp-up --train train.lex --devel 5% --write-model model-2
g2p.py --model model-2 --test test.lex > model-2.test
g2p.py --model model-2 --ramp-up --train train.lex --devel 5% --write-model model-3
g2p.py --model model-3 --test test.lex > model-3.test
g2p.py --model model-3 --ramp-up --train train.lex --devel 5% --write-model model-4
g2p.py --model model-4 --test test.lex > model-4.test
g2p.py --model model-4 --ramp-up --train train.lex --devel 5% --write-model model-5
g2p.py --model model-5 --test test.lex > model-5.test
g2p.py --model model-5 --ramp-up --train train.lex --devel 5% --write-model model-6
g2p.py --model model-6 --test test.lex > model-6.test

# useful to check for inconsitencies in manual entries
g2p.py --model model-6 --test all.lex > model-6-all.test

#
# these show no improvements in my tests so far:
#

# g2p.py --model model-6 --ramp-up --train train.lex --devel 5% --write-model model-7
# g2p.py --model model-7 --test test.lex > model-7.test
# g2p.py --model model-7 --ramp-up --train train.lex --devel 5% --write-model model-8 
# g2p.py --model model-8 --test test.lex > model-8.test
# g2p.py --model model-8 --ramp-up --train train.lex --devel 5% --write-model model-9
# g2p.py --model model-9 --test test.lex > model-9.test
# g2p.py --model model-9 --ramp-up --train train.lex --devel 5% --write-model model-10
# g2p.py --model model-10 --test test.lex > model-10.test

