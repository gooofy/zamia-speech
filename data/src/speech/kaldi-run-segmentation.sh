#!/bin/bash

# Copyright 2018  Guenter Bartsch
# Copyright 2016  Vimal Manohar
# Apache 2.0

. ./cmd.sh
. ./path.sh

# set -e -o pipefail -u

#
# segmentation options
#
# Uniform segmentation options
max_segment_duration=30 # 
overlap_duration=5
seconds_per_spk_max=30

# First-pass segmentation opts
# These options are passed to the script
# steps/cleanup/internal/segment_ctm_edits_mild.py

min_split_point_duration=0.1              # Minimum duration of silence or non-scored word to be 
                                          # considered a viable split point when truncating based on junk proportion.
                                          # Default: 0.0
max_deleted_words_kept_when_merging=1     # When merging segments that are found to be overlapping or adjacent after 
                                          # all other processing, keep in the transcript the reference words that were
                                          # deleted between the segments [if any] as long as there were no more than 
                                          # this many reference words.  Setting this to zero will mean that any 
                                          # reference words that were deleted between the segments we're about to
                                          # reattach will not appear in the generated transcript (so we'll match the hyp).
                                          # Default: 1
max_wer=50                                # Max WER%% of merged segments when merging. 
                                          # Default: 10.0
max_segment_length_for_merging=60         # Maximum segment length allowed for merged segment
                                          # Default: 10
max_bad_proportion=0.75                   # Maximum length of silence, junk and incorrect words in a merged segment 
                                          # allowed as a fraction of the total length of merged segment.
                                          # Default: 0.2
# max_bad_proportion=0.5
max_intersegment_incorrect_words_length=1 # Maximum length of intersegment region that can be of incorrect word. This is to
                                          # allow cases where there may be a lot of silence in the segment but the incorrect 
                                          # words are few, while preventing regions that have a lot of incorrect words.
                                          # Default: 0.2
max_segment_length_for_splitting=10       # Try to split long segments into segments that are smaller that this size.
                                          # Default: 10
hard_max_segment_length=15                # Split all segments that are longer than this uniformly into segments of size 
                                          # max-segment-length. 
                                          # Default: 15
min_silence_length_to_split_at=0.3        # Only considers silences that are at least this long as potential split points
                                          # Default: 0.3
min_non_scored_length_to_split_at=0.3     # Only considers non-scored words that are at least this long as potential split points
                                          # Default: 0.1

. utils/parse_options.sh

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

    steps/cleanup/segment_long_utterances.sh --cmd "$train_cmd" \
      --stage $segment_stage --nj 4 \
      --max_segment_duration $max_segment_duration \
      --overlap_duration $overlap_duration \
      --seconds_per_spk_max $seconds_per_spk_max \
      --min_split_point_duration $min_split_point_duration \
      --max_deleted_words_kept_when_merging $max_deleted_words_kept_when_merging \
      --max_wer $max_wer \
      --max_segment_length_for_merging $max_segment_length_for_merging \
      --max_bad_proportion $max_bad_proportion \
      --max_intersegment_incorrect_words_length $max_intersegment_incorrect_words_length \
      --max_segment_length_for_splitting $max_segment_length_for_splitting \
      --hard_max_segment_length $hard_max_segment_length \
      --min_silence_length_to_split_at $min_silence_length_to_split_at \
      --min_non_scored_length_to_split_at $min_non_scored_length_to_split_at \
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

