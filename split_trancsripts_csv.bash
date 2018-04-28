#!/bin/bash

# Split contents of data/src/speech/de/transcripts_*.csv according to corpus
#
# Target directory and file structure:
#
#     src/
#       speech/
#         forschergeist/
#           spk2gender
#           transcripts_00.csv
#         gspv2/
#           spk2gender
#           spk_test.txt
#           transcripts_00.csv
#         voxforge_de/
#           spk2gender
#           spk_test.txt
#           transcripts_00.csv
#           transcripts_01.csv
#         zamia_de/
#           spk2gender
#           spk_test.txt
#           transcripts_00.csv
#
# This script assumes that all entries in data/src/speech/de/transcripts_*.csv
# that ...
#
# 1) ... start with 'timpritlove' or 'annettevogt' belong to the Forschergeist
#    corpus.
#
# 2) ... start with 'gsp' belong to the corpus German Speechpackage Version 2.
#
# 3) ...
#        a) don't start with 'gsp'
#        b) and don't start with 'timpritlove'
#        c) and don't start with 'annettevogt'
#        d) and don't start with the entries given in zamia_de_speakers.txt
#    belong to the German VoxForge corpus, i.e. also entries starting with
#    'phone' and 'noisy'.
#
# 4) ... start with the entries given in zamia_de_speakers.txt belong to the
#    corpus zamia_de.
#

set -euo pipefail

TRANSCRIPTS_DIR=data/src/speech/de

TARGET_DIR_FORSCHERGEIST=data/src/speech/forschergeist
TARGET_DIR_GSPV2=data/src/speech/gspv2
TARGET_DIR_VOXFORGE=data/src/speech/voxforge_de
TARGET_DIR_ZAMIA_DE=data/src/speech/zamia_de

main() {
    process_forschergeist
    process_gspv2
    process_voxforge_de
    process_zamia_de
}

process_forschergeist() {
    mkdir -p ${TARGET_DIR_FORSCHERGEIST}

    cat ${TRANSCRIPTS_DIR}/transcripts_*.csv \
        | filter_forschergeist \
              > "${TARGET_DIR_FORSCHERGEIST}/transcripts_00.csv"

    cat ${TRANSCRIPTS_DIR}/spk2gender \
        | filter_forschergeist \
              > "${TARGET_DIR_FORSCHERGEIST}/spk2gender"
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

process_voxforge_de() {
    mkdir -p ${TARGET_DIR_VOXFORGE}
    cat ${TRANSCRIPTS_DIR}/transcripts_*.csv \
        | filter_voxforge_de \
              > "${TARGET_DIR_VOXFORGE}/transcripts_00.csv"
}

process_zamia_de() {
    mkdir -p ${TARGET_DIR_ZAMIA_DE}
    cat ${TRANSCRIPTS_DIR}/transcripts_*.csv \
        | filter_zamia_de \
              > "${TARGET_DIR_ZAMIA_DE}/transcripts_00.csv"

    cat ${TRANSCRIPTS_DIR}/spk2gender \
        | filter_zamia_de \
              > "${TARGET_DIR_ZAMIA_DE}/spk2gender"

    cat ${TRANSCRIPTS_DIR}/spk_test.txt \
        | filter_zamia_de \
              > "${TARGET_DIR_ZAMIA_DE}/spk_test.txt"
}

filter_forschergeist() {
    grep -e '^timpritlove' -e '^annettevogt'
}

filter_gspv2() {
    grep '^gsp'
}

filter_voxforge_de() {
    grep -v -e '^gsp' -e '^timpritlove' -e '^annettevogt' -f zamia_de_speakers.txt
}

filter_zamia_de() {
    grep -f zamia_de_speakers.txt
}

main
