#!/bin/bash

VOICE=elliot

./ztts_train.py -v ${VOICE} 2>&1 | tee train_${VOICE}.log

