#!/bin/bash

# Copyright 2018  Guenter Bartsch
# Copyright 2016  Vimal Manohar
# Apache 2.0

. ./cmd.sh
. ./path.sh

# set -e -o pipefail -u

mfccdir=mfcc_segmentation

segment_stage=-9
cleanup_stage=-1
cleanup_affix=cleaned_b
affix=_a

lmdir=data/local/lm

stage=0

# export nJobs=1
# export nDecodeJobs=8

#
# adapt model to latest dict
#

if [ $stage -le 1 ]; then

    rm -rf data/lang.adapt
    
    # Prepare phoneme data for Kaldi
    utils/prepare_lang.sh data/local/dict.adapt "nspc" data/local/lang data/lang.adapt
    
    rm -rf data/lang_test.adapt
    cp -r data/lang.adapt data/lang_test.adapt

fi

if [ $stage -le 2 ]; then

    echo
    echo "creating G.fst..."

    cat ../srilm/lm.arpa | utils/find_arpa_oovs.pl data/lang_test.adapt/words.txt  > $lmdir/oovs_lm_adapt.txt

    echo "creating G.fst...2"

    cat ../srilm/lm.arpa | \
        grep -v '<s> <s>' | \
        grep -v '</s> <s>' | \
        grep -v '</s> </s>' | \
        arpa2fst - | fstprint | \
        utils/remove_oovs.pl $lmdir/oovs_lm_adapt.txt | \
        utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=data/lang_test.adapt/words.txt \
          --osymbols=data/lang_test.adapt/words.txt  --keep_isymbols=false --keep_osymbols=false | \
         fstrmepsilon > data/lang_test.adapt/G.fst
fi

if [ $stage -le 3 ]; then

    echo "tri2b_adapt... "
    rm -rf exp/tri2b_adapt
    cp -r exp/tri2b_chain exp/tri2b_adapt
    rm -rf exp/tri2b_adapt/graph

    utils/mkgraph.sh data/lang_test.adapt exp/tri2b_adapt exp/tri2b_adapt/graph || exit 1;

fi


#
# make mfcc
#

if [ $stage -le 4 ]; then

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

steps/cleanup/segment_long_utterances.sh --cmd "$train_cmd" \
  --stage $segment_stage --nj 4 \
  --max-bad-proportion 0.5 \
  exp/tri2b_adapt data/lang data/segmentation data/segmentation_result${affix} \
  exp/segment_long_utts${affix}_train

steps/compute_cmvn_stats.sh data/segmentation_result${affix} \
  exp/make_mfcc/segmentation_result${affix} mfcc
utils/fix_data_dir.sh data/segmentation_result${affix}

###############################################################################
# Train new model on segmented data directory starting from the same model
# used for segmentation. (tri2b_adapt_reseg)
###############################################################################

# Align tri2b_adapt system with reseg${affix} data
steps/align_si.sh  --nj 12 --cmd "$train_cmd" \
  data/segmentation_result${affix} \
  data/lang exp/tri2b_adapt exp/tri2b_adapt_ali_reseg${affix}  || exit 1;


# Train LDA+MLLT system on reseg${affix} data
steps/train_lda_mllt.sh --cmd "$train_cmd" \
  4000 50000 data/segmentation_result${affix} data/lang \
  exp/tri2b_adapt_ali_reseg${affix} exp/tri2b_adapt_reseg${affix}

###############################################################################
# Train SAT model on segmented data directory
###############################################################################

# Train SAT system on reseg${affix} data
steps/train_sat.sh --cmd "$train_cmd" 5000 100000 \
  data/segmentation_result${affix} data/lang \
  exp/tri2b_adapt_reseg${affix} exp/tri3_reseg${affix}

###############################################################################
# Clean and segment data
###############################################################################

segmentation_opts=(
--max-junk-proportion=0.5
--max-deleted-words-kept-when-merging=10
)
opts="${segmentation_opts[@]}"

steps/cleanup/clean_and_segment_data.sh --nj 12 --cmd "$train_cmd" \
  --segmentation-opts "$opts" \
  data/segmentation_result${affix} data/lang exp/tri3_reseg${affix} \
  exp/tri3_reseg${affix}_${cleanup_affix}_work \
  data/segmentation_result${affix}_${cleanup_affix}

wait
exit 0

