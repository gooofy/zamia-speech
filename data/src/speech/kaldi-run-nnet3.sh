#!/bin/bash

#
# Copyright 2016 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# adapted from kaldi's wsj egs

stage=0
train_stage=-10
dir=exp/nnet3/nnet_tdnn_a
mfccdir=mfcc

# remove old lang dir if it exists
rm -rf data/lang

# now start preprocessing with KALDI scripts

if [ -f cmd.sh ]; then
      . cmd.sh; else
         echo "missing cmd.sh"; exit 1;
fi

# Path also sets LC_ALL=C for Kaldi, otherwise you will experience strange (and hard to debug!) bugs. It should be set here, after the python scripts and not at the beginning of this script
if [ -f path.sh ]; then
      . path.sh; else
         echo "missing path.sh"; exit 1;

fi

echo "Runtime configuration is: nJobs $nJobs, nDecodeJobs $nDecodeJobs. If this is not what you want, edit cmd.sh"

# Prepare phoneme data for Kaldi
utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang

# At this script level we don't support not running on GPU, as it would be painfully slow.
# If you want to run without GPU you'd have to call train_tdnn.sh with --gpu false,
# --num-threads 16 and --minibatch-size 128.

if ! cuda-compiled; then
  cat <<EOF && exit 1
This script is intended to be used with GPUs but you have not compiled Kaldi with CUDA
If you want to use GPUs (and have them), go to src/, and configure and make on a machine
where "nvcc" is installed.
EOF
fi

#
# make hires mfcc
#

for datadir in train test; do
    utils/fix_data_dir.sh data/$datadir 
    utils/copy_data_dir.sh data/$datadir data/${datadir}_hires
    steps/make_mfcc.sh --nj $nJobs --mfcc-config conf/mfcc_hires.conf \
      --cmd "$train_cmd" data/${datadir}_hires exp/make_hires/$datadir $mfccdir || exit 1;
    steps/compute_cmvn_stats.sh data/${datadir}_hires exp/make_hires/$datadir $mfccdir || exit 1;
done

#
# mono0a_hires
#

echo
echo mono0a_hires
echo

steps/train_mono.sh --nj $nJobs --cmd "$train_cmd" \
  data/train_hires data/lang exp/mono0a_hires || exit 1;

#
# tri1_hires
#

echo
echo tri1_hires
echo

steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  data/train_hires data/lang exp/mono0a_hires exp/mono0a_ali_hires || exit 1;

steps/train_deltas.sh --cmd "$train_cmd" 2000 10000 \
  data/train_hires data/lang exp/mono0a_ali_hires exp/tri1_hires || exit 1;

#
# tri2b_hires
#

echo
echo tri2b_hires
echo

steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  data/train_hires data/lang exp/tri1_hires exp/tri1_ali_hires || exit 1;

steps/train_lda_mllt.sh --cmd "$train_cmd" \
  --splice-opts "--left-context=3 --right-context=3" 2500 15000 \
  data/train_hires data/lang exp/tri1_ali_hires exp/tri2b_hires || exit 1;

utils/mkgraph.sh data/lang_test \
  exp/tri2b_hires exp/tri2b_hires/graph || exit 1;

# #
# # tri3b_hires 
# #
# 
# # Align tri2b system with sub data.
# steps/align_si.sh  --nj $nJobs --cmd "$train_cmd" \
#   --use-graphs true data/train_hires \
#   data/lang exp/tri2b_hires exp/tri2b_ali_hires  || exit 1;
# 
# # From 2b system, train 3b which is LDA + MLLT + SAT.
# steps/train_sat.sh --cmd "$train_cmd" 2500 15000 \
#   data/train_hires data/lang exp/tri2b_ali_hires exp/tri3b_hires || exit 1;


echo #############################################################################################################
echo # ivector code
echo #############################################################################################################


# if [ $stage -le 2 ]; then
#   # We need to build a small system just because we need the LDA+MLLT transform
#   # to train the diag-UBM on top of.  We align the subset data for this purpose.
# 
#   steps/align_fmllr.sh --nj $nJobs --cmd "$train_cmd" \
#     data/train_subset_hires data/lang exp/tri4b exp/nnet3/tri4b_ali_subset
# fi
# 
# if [ $stage -le 3 ]; then
#   # Train a small system just for its LDA+MLLT transform.  We use --num-iters 13
#   # because after we get the transform (12th iter is the last), any further
#   # training is pointless.
#   steps/train_lda_mllt.sh --cmd "$train_cmd" --num-iters 13 \
#     --realign-iters "" \
#     --splice-opts "--left-context=3 --right-context=3" \
#     5000 10000 data/train_subset_hires data/lang \
#      exp/nnet3/tri4b_ali_subset exp/nnet3/tri5b
# fi

mkdir -p exp/nnet3

# steps/online/nnet2/train_diag_ubm.sh --cmd "$train_cmd" --nj $nJobs \
#    --num-frames 400000 data/train_hires 256 exp/nnet3/tri5b exp/nnet3/diag_ubm || exit 1;

steps/online/nnet2/train_diag_ubm.sh --cmd "$train_cmd" --nj $nJobs \
   --num-frames 400000 data/train_hires 256 exp/tri2b_hires exp/nnet3/diag_ubm || exit 1;

echo
echo exp/nnet3/extractor
echo

# even though $nj is just 4, each job uses multiple processes and threads.
steps/online/nnet2/train_ivector_extractor.sh --cmd "$train_cmd" --nj 4 \
   data/train_hires exp/nnet3/diag_ubm exp/nnet3/extractor || exit 1;

echo
echo exp/nnet3/ivectors_train
echo

# We extract iVectors on all the train data, which will be what we
# train the system on.

# having a larger number of speakers is helpful for generalization, and to
# handle per-utterance decoding well (iVector starts at zero).
steps/online/nnet2/copy_data_dir.sh --utts-per-spk-max 2 data/train_hires \
  data/train_hires_max2

steps/online/nnet2/extract_ivectors_online.sh --cmd "$train_cmd" --nj $nJobs \
  data/train_hires_max2 exp/nnet3/extractor exp/nnet3/ivectors_train || exit 1;


echo
echo extract_ivectors_online.sh
echo

rm exp/nnet3/.error 2>/dev/null
for data in test; do
  steps/online/nnet2/extract_ivectors_online.sh --cmd "$train_cmd" --nj $nJobs \
    data/${data}_hires exp/nnet3/extractor exp/nnet3/ivectors_${data} || touch exp/nnet3/.error 
done
[ -f exp/nnet3/.error ] && echo "$0: error extracting iVectors." && exit 1;

echo
echo train_tdnn.sh
echo

steps/nnet3/train_tdnn.sh --stage $train_stage \
  --num-epochs 8 --num-jobs-initial 2 --num-jobs-final 14 \
  --splice-indexes "-4,-3,-2,-1,0,1,2,3,4  0  -2,2  0  -4,4 0" \
  --feat-type raw \
  --online-ivector-dir exp/nnet3/ivectors_train \
  --cmvn-opts "--norm-means=false --norm-vars=false" \
  --initial-effective-lrate 0.005 --final-effective-lrate 0.0005 \
  --cmd "$decode_cmd" \
  --pnorm-input-dim 2000 \
  --pnorm-output-dim 250 \
  --minibatch-size 128 \
  data/train_hires data/lang exp/tri1_ali_hires exp/nnet3/nnet_tdnn_a  || exit 1;

echo
echo mkgraph
echo

utils/mkgraph.sh data/lang_test \
  exp/nnet3/nnet_tdnn_a exp/nnet3/nnet_tdnn_a/graph || exit 1;

echo
echo decode
echo

steps/nnet3/decode.sh --nj $nDecodeJobs --cmd "$decode_cmd" \
    --online-ivector-dir exp/nnet3/ivectors_test \
   exp/nnet3/nnet_tdnn_a/graph data/test_hires exp/nnet3/nnet_tdnn_a/decode || exit 1;

grep WER exp/nnet3/nnet_tdnn_a/decode/scoring_kaldi/best_wer >>RESULTS.txt

echo #############################################################################################################
echo # LSTM
echo #############################################################################################################

# this is a basic lstm script
# LSTM script runs for more epochs than the TDNN script
# and each epoch takes twice the time

# At this script level we don't support not running on GPU, as it would be painfully slow.
# If you want to run without GPU you'd have to call lstm/train.sh with --gpu false

stage=0
train_stage=-10
affix=
common_egs_dir=

# LSTM options
splice_indexes="-2,-1,0,1,2 0 0"
lstm_delay=" -1 -2 -3 "
label_delay=5
num_lstm_layers=3
cell_dim=1024
hidden_dim=1024
recurrent_projection_dim=256
non_recurrent_projection_dim=256
chunk_width=20
chunk_left_context=40
chunk_right_context=0


# training options
num_epochs=10
initial_effective_lrate=0.0006
final_effective_lrate=0.00006
num_jobs_initial=2
num_jobs_final=6
#num_jobs_final=12
momentum=0.5
#num_chunk_per_minibatch=100
num_chunk_per_minibatch=50
samples_per_iter=20000
remove_egs=true

#decode options
extra_left_context=
extra_right_context=
frames_per_chunk=

dir=exp/nnet3/lstm
dir=$dir${affix:+_$affix}
if [ $label_delay -gt 0 ]; then dir=${dir}_ld$label_delay; fi

steps/nnet3/lstm/train.sh --stage $train_stage \
  --label-delay $label_delay \
  --lstm-delay "$lstm_delay" \
  --num-epochs $num_epochs --num-jobs-initial $num_jobs_initial --num-jobs-final $num_jobs_final \
  --num-chunk-per-minibatch $num_chunk_per_minibatch \
  --samples-per-iter $samples_per_iter \
  --splice-indexes "$splice_indexes" \
  --feat-type raw \
  --online-ivector-dir exp/nnet3/ivectors_train \
  --cmvn-opts "--norm-means=false --norm-vars=false" \
  --initial-effective-lrate $initial_effective_lrate --final-effective-lrate $final_effective_lrate \
  --momentum $momentum \
  --cmd "$decode_cmd" \
  --num-lstm-layers $num_lstm_layers \
  --cell-dim $cell_dim \
  --hidden-dim $hidden_dim \
  --recurrent-projection-dim $recurrent_projection_dim \
  --non-recurrent-projection-dim $non_recurrent_projection_dim \
  --chunk-width $chunk_width \
  --chunk-left-context $chunk_left_context \
  --chunk-right-context $chunk_right_context \
  --egs-dir "$common_egs_dir" \
  --remove-egs $remove_egs \
  data/train_hires data/lang exp/tri1_ali_hires $dir  || exit 1;

echo
echo mkgraph
echo

utils/mkgraph.sh data/lang_test \
  $dir $dir/graph || exit 1;

echo
echo decode
echo

if [ -z $extra_left_context ]; then
    extra_left_context=$chunk_left_context
fi
if [ -z $extra_right_context ]; then
    extra_right_context=$chunk_right_context
fi
if [ -z $frames_per_chunk ]; then
    frames_per_chunk=$chunk_width
fi

steps/nnet3/lstm/decode.sh --nj $nDecodeJobs --cmd "$decode_cmd" \
	  --extra-left-context $extra_left_context \
	  --extra-right-context $extra_right_context \
	  --frames-per-chunk "$frames_per_chunk" \
	  --online-ivector-dir exp/nnet3/ivectors_test \
	 $dir/graph data/test_hires $dir/decode || exit 1;

# grep WER $dir/decode/scoring_kaldi/best_wer
cat exp/nnet3/lstm_ld5/decode/scoring_kaldi/best_wer >>RESULTS.txt

