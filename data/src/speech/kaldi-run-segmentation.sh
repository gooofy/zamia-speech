#!/bin/bash

# Copyright 2018  Guenter Bartsch
# Copyright 2016  Vimal Manohar
# Apache 2.0

. ./cmd.sh
. ./path.sh

# set -e -o pipefail -u

mfccdir=mfcc_segmentation

segment_stage=-9
cleanup_affix=cleaned_b
affix=_a

stage=0

#
# make mfcc
#

if [ $stage -le 0 ]; then

    echo "make mfcc... "

    rm -rf $mfccdir
    mkdir $mfccdir

    for datadir in segmentation; do
        utils/fix_data_dir.sh data/$datadir 
        steps/make_mfcc.sh --cmd "$train_cmd" --nj 4 data/$datadir exp/make_mfcc_segmentation/$datadir $mfccdir || exit 1;
        utils/fix_data_dir.sh data/${datadir} # some files fail to get mfcc for many reasons
        steps/compute_cmvn_stats.sh data/${datadir} exp/make_mfcc_segmentation/$datadir $mfccdir || exit 1;
        utils/fix_data_dir.sh data/${datadir} # some files fail to get mfcc for many reasons
    done

fi


###############################################################################
# Segment long recordings using TF-IDF retrieval of reference text 
# for uniformly segmented audio chunks based on Smith-Waterman alignment.
# use our a model from our nnet3 chain run (tri2b_adapt)
###############################################################################

if [ $stage -le 1 ]; then

    # FIXME: kaldi bug? - phones.txt is not copied but required so
    #        we copy it here beforehand
    mkdir -p exp/segment_long_utts_a_train
    cp data/lang/phones.txt exp/segment_long_utts_a_train/

    # FIXME: expose segmentation opts
    #
    # # Uniform segmentation options
    # max_segment_duration=30
    # overlap_duration=5
    # seconds_per_spk_max=30a
    #
    # # First-pass segmentation opts
    # # These options are passed to the script
    # # steps/cleanup/internal/segment_ctm_edits_mild.py
    # segmentation_extra_opts=
    # min_split_point_duration=0.1
    # max_deleted_words_kept_when_merging=1
    # max_wer=50
    # max_segment_length_for_merging=60
    # max_bad_proportion=0.75
    # max_intersegment_incorrect_words_length=1
    # max_segment_length_for_splitting=10
    # hard_max_segment_length=15
    # min_silence_length_to_split_at=0.3
    # min_non_scored_length_to_split_at=0.3

    steps/cleanup/segment_long_utterances.sh --cmd "$train_cmd" \
      --stage $segment_stage --nj 4 \
      --max-bad-proportion 0.5 \
      exp/tri2b_adapt data/lang data/segmentation data/segmentation_result${affix} \
      exp/segment_long_utts${affix}_train

    steps/compute_cmvn_stats.sh data/segmentation_result${affix} \
      exp/make_mfcc/segmentation_result${affix} mfcc
    utils/fix_data_dir.sh data/segmentation_result${affix}

fi

###############################################################################
# Train new model on segmented data directory starting from the same model
# used for segmentation. (tri2b_adapt_reseg)
###############################################################################

if [ $stage -le 2 ]; then

    # Align tri2b_adapt system with reseg${affix} data
    steps/align_si.sh  --nj 12 --cmd "$train_cmd" \
      data/segmentation_result${affix} \
      data/lang exp/tri2b_adapt exp/tri2b_adapt_ali_reseg${affix}  || exit 1;

    # Train LDA+MLLT system on reseg${affix} data
    steps/train_lda_mllt.sh --cmd "$train_cmd" \
      4000 50000 data/segmentation_result${affix} data/lang \
      exp/tri2b_adapt_ali_reseg${affix} exp/tri2b_adapt_reseg${affix}

fi

###############################################################################
# Train SAT model on segmented data directory
###############################################################################

if [ $stage -le 3 ]; then

    # Train SAT system on reseg${affix} data
    steps/train_sat.sh --cmd "$train_cmd" 5000 100000 \
      data/segmentation_result${affix} data/lang \
      exp/tri2b_adapt_reseg${affix} exp/tri3_reseg${affix}
fi

###############################################################################
# Clean and segment data
###############################################################################

segmentation_opts=(
--max-junk-proportion=0.5
--max-deleted-words-kept-when-merging=10
)
opts="${segmentation_opts[@]}"

if [ $stage -le 4 ]; then

    steps/cleanup/clean_and_segment_data.sh --nj 12 --cmd "$train_cmd" \
      --segmentation-opts "$opts" \
      data/segmentation_result${affix} data/lang exp/tri3_reseg${affix} \
      exp/tri3_reseg${affix}_${cleanup_affix}_work \
      data/segmentation_result${affix}_${cleanup_affix}

fi

wait
exit 0

