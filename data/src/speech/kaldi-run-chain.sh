#!/bin/bash

#
# Copyright 2016, 2017 Guenter Bartsch
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
# adapted from kaldi's librispeech egs

mfccdir=mfcc_chain

stage=0
min_seg_len=1.55
train_set=train
gmm=tri2b_chain # the gmm for the target data
nnet3_affix=_chain  # cleanup affix for nnet3 and chain dirs, e.g. _cleaned

# The rest are configs specific to this script.  Most of the parameters
# are just hardcoded at this level, in the commands below.
train_stage=-10
get_egs_stage=-10
num_chunk_per_minibatch=128
 
# TDNN options
# this script uses the new tdnn config generator so it needs a final 0 to reflect that the final layer input has no splicing
# training options
frames_per_eg=150
relu_dim=725
remove_egs=false
common_egs_dir=
xent_regularize=0.1
self_repair_scale=0.00001

# pre-flight checks

if [ -f cmd.sh ]; then
      . cmd.sh; else
         echo "missing cmd.sh"; exit 1;
fi

# Path also sets LC_ALL=C for Kaldi, otherwise you will experience strange (and hard to debug!) bugs. It should be set here, after the python scripts and not at the beginning of this script
if [ -f path.sh ]; then
      . path.sh; else
         echo "missing path.sh"; exit 1;

fi

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

echo "Runtime configuration is: nJobs $nJobs, nDecodeJobs $nDecodeJobs. If this is not what you want, edit cmd.sh"

# now start preprocessing with KALDI scripts

# remove old lang dir if it exists
rm -rf data/lang

# Prepare phoneme data for Kaldi
# utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang
utils/prepare_lang.sh data/local/dict "nspc" data/local/lang data/lang

#
# make mfcc
#

for datadir in train test; do
    utils/fix_data_dir.sh data/$datadir 
    steps/make_mfcc.sh --cmd "$train_cmd" --nj $nJobs data/$datadir exp/make_mfcc_chain/$datadir $mfccdir || exit 1;
    utils/fix_data_dir.sh data/${datadir} # some files fail to get mfcc for many reasons
    steps/compute_cmvn_stats.sh data/${datadir} exp/make_mfcc_chain/$datadir $mfccdir || exit 1;
    utils/fix_data_dir.sh data/${datadir} # some files fail to get mfcc for many reasons
done

echo
echo mono0a_chain
echo

steps/train_mono.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/mono0a_chain || exit 1;

echo
echo tri1_chain
echo

steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/mono0a_chain exp/mono0a_ali_chain || exit 1;

steps/train_deltas.sh --cmd "$train_cmd" 2000 10000 \
  data/train data/lang exp/mono0a_ali_chain exp/tri1_chain || exit 1;

echo
echo tri2b_chain
echo

steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/tri1_chain exp/tri1_ali_chain || exit 1;

steps/train_lda_mllt.sh --cmd "$train_cmd" \
  --splice-opts "--left-context=3 --right-context=3" 2500 15000 \
  data/train data/lang exp/tri1_ali_chain exp/tri2b_chain || exit 1;

utils/mkgraph.sh data/lang_test \
  exp/tri2b_chain exp/tri2b_chain/graph || exit 1;

echo
echo run_ivector_common.sh
echo

local/nnet3/run_ivector_common.sh --stage $stage \
                                  --min-seg-len $min_seg_len \
                                  --train-set $train_set \
                                  --gmm $gmm \
                                  --nnet3-affix "$nnet3_affix" || exit 1;

gmm_dir=exp/$gmm
ali_dir=exp/${gmm}_ali_${train_set}_sp_comb
tree_dir=exp/nnet3${nnet3_affix}/tree_sp
lang=data/lang_chain
lat_dir=exp/nnet3${nnet3_affix}/${gmm}_${train_set}_sp_comb_lats
dir=exp/nnet3${nnet3_affix}/tdnn_sp
train_data_dir=data/${train_set}_sp_hires_comb
lores_train_data_dir=data/${train_set}_sp_comb
train_ivector_dir=exp/nnet3${nnet3_affix}/ivectors_${train_set}_sp_hires_comb

for f in $gmm_dir/final.mdl $train_data_dir/feats.scp $train_ivector_dir/ivector_online.scp \
    $lores_train_data_dir/feats.scp $ali_dir/ali.1.gz; do
  [ ! -f $f ] && echo "$0: expected file $f to exist" && exit 1
done

echo
echo run_chain_common.sh
echo
# Please take this as a reference on how to specify all the options of
# local/chain/run_chain_common.sh  
local/chain/run_chain_common.sh --stage $stage \
                                --gmm-dir $gmm_dir \
                                --ali-dir $ali_dir \
                                --lores-train-data-dir ${lores_train_data_dir} \
                                --lang $lang \
                                --lat-dir $lat_dir \
                                --tree-dir $tree_dir || exit 1;

echo
echo "$0: creating neural net configs";
echo 
mkdir -p $dir

# create the config files for nnet initialization
repair_opts=${self_repair_scale:+" --self-repair-scale-nonlinearity $self_repair_scale "}

steps/nnet3/tdnn/make_configs.py $repair_opts \
  --feat-dir $train_data_dir \
  --ivector-dir $train_ivector_dir \
  --tree-dir $tree_dir \
  --relu-dim $relu_dim \
  --splice-indexes "-1,0,1 -1,0,1,2 -3,0,3 -3,0,3 -3,0,3 -6,-3,0 0" \
  --use-presoftmax-prior-scale false \
  --xent-regularize $xent_regularize \
  --xent-separate-forward-affine true \
  --include-log-softmax false \
  --final-layer-normalize-target 0.5 \
  $dir/configs || exit 1;

echo
echo train.py 
echo

touch $dir/egs/.nodelete # keep egs around when that run dies.

steps/nnet3/chain/train.py --stage $train_stage \
  --cmd "$decode_cmd" \
  --feat.online-ivector-dir $train_ivector_dir \
  --feat.cmvn-opts "--norm-means=false --norm-vars=false" \
  --chain.xent-regularize $xent_regularize \
  --chain.leaky-hmm-coefficient 0.1 \
  --chain.l2-regularize 0.00005 \
  --chain.apply-deriv-weights false \
  --chain.lm-opts="--num-extra-lm-states=2000" \
  --egs.stage $get_egs_stage \
  --egs.opts "--frames-overlap-per-eg 0" \
  --egs.chunk-width $frames_per_eg \
  --egs.dir "$common_egs_dir" \
  --trainer.num-chunk-per-minibatch $num_chunk_per_minibatch \
  --trainer.frames-per-iter 1500000 \
  --trainer.num-epochs 4 \
  --trainer.optimization.num-jobs-initial 1 \
  --trainer.optimization.num-jobs-final 1 \
  --trainer.optimization.initial-effective-lrate 0.001 \
  --trainer.optimization.final-effective-lrate 0.0001 \
  --trainer.max-param-change 2 \
  --cleanup.remove-egs $remove_egs \
  --feat-dir $train_data_dir \
  --tree-dir $tree_dir \
  --lat-dir $lat_dir \
  --dir $dir  || exit 1;

echo
echo mkgraph
echo

graph_dir=$dir/graph

utils/mkgraph.sh --self-loop-scale 1.0 --remove-oov data/lang_test $dir $graph_dir
# remove <UNK> from the graph
fstrmsymbols --apply-to-output=true --remove-arcs=true "echo 3|" $graph_dir/HCLG.fst $graph_dir/HCLG.fst

echo
echo decode
echo

steps/nnet3/decode.sh --acwt 1.0 --post-decode-acwt 10.0 \
    --nj $nDecodeJobs --cmd "$decode_cmd" \
    --online-ivector-dir exp/nnet3${nnet3_affix}/ivectors_test_hires \
    $graph_dir data/test_hires $dir/decode_test || exit 1

grep WER exp/nnet3_chain/tdnn_sp/decode_test/scoring_kaldi/best_wer >>RESULTS.txt

