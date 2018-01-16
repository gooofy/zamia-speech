#!/usr/bin/env bash

conda env export -n gooofy-speech |\
    grep -v "^prefix:" \
    > environment.yml
