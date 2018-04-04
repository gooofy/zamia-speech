#!/bin/bash

# Split contents of data/src/speech/de/transcripts_*.csv according to corpus
#
# Target directory and file structure:
#
#     src/
#       speech/
#         voxforge_de/
#           spk2gender
#           spk_test.txt
#           transcripts_00.csv
#           transcripts_01.csv
#         gspv2/
#           spk2gender
#           spk_test.txt
#           transcripts_00.csv
#
# This script assumes that
#
# 1) all entries in transcripts_*.csv that start with
#    'gsp' belong to the corpus German Speechpackage Version 2.
#
# 2) all entries in transcripts_*.csv that don't start with 'gsp' belong
#    to the German VoxForge corpus, i.e. also entries starting with 'phone'
#    and 'noisy'.

set -euo pipefail

TRANSCRIPTS_DIR=data/src/speech/de

TARGET_DIR_VOXFORGE=data/src/speech/voxforge_de
TARGET_DIR_GSPV2=data/src/speech/gspv2

main() {
    process_voxforge_de
    process_gspv2
}

process_voxforge_de() {
    mkdir -p ${TARGET_DIR_VOXFORGE}
    cat ${TRANSCRIPTS_DIR}/transcripts_*.csv \
        | filter_voxforge_de \
              > "${TARGET_DIR_VOXFORGE}/transcripts_00.csv"

    cat ${TRANSCRIPTS_DIR}/spk2gender \
        | filter_voxforge_de \
              > "${TARGET_DIR_VOXFORGE}/spk2gender"

    cat ${TRANSCRIPTS_DIR}/spk_test.txt \
        | filter_voxforge_de \
              > "${TARGET_DIR_VOXFORGE}/spk_test.txt"
}

process_gspv2() {
    mkdir -p ${TARGET_DIR_GSPV2}
    cat ${TRANSCRIPTS_DIR}/transcripts_*.csv \
        | filter_gspv2 \
              > "${TARGET_DIR_GSPV2}/transcripts_00.csv"

    cat ${TRANSCRIPTS_DIR}/spk2gender \
        | filter_gspv2 \
              > "${TARGET_DIR_GSPV2}/spk2gender"

    cat ${TRANSCRIPTS_DIR}/spk_test.txt \
        | filter_gspv2 \
              > "${TARGET_DIR_GSPV2}/spk_test.txt"
}

filter_voxforge_de() {
    grep -v -e '^gsp'
}

filter_gspv2() {
    grep '^gsp'
}

main
