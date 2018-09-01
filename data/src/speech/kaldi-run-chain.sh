#!/bin/bash

#
# Copyright 2016, 2017, 2018 Guenter Bartsch
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
# adapted from kaldi's egs/tedlium/s5_r2/local/chain/run_tdnn.sh

mfccdir=mfcc_chain

stage=0
min_seg_len=1.55
train_set=train
gmm=tri2b_chain # the gmm for the target data
nnet3_affix=_chain  # cleanup affix for nnet3 and chain dirs, e.g. _cleaned
num_threads_ubm=12
get_egs_stage=-10

xent_regularize=0.1
train_stage=-10
common_egs_dir=  # you can set this to use previously dumped egs.
dropout_schedule='0,0@0.20,0.5@0.50,0'
frames_per_eg=150,110,100

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

. utils/parse_options.sh

echo "Runtime configuration is: nJobs $nJobs, nDecodeJobs $nDecodeJobs. If this is not what you want, edit cmd.sh"
echo "Starting at stage $stage, train_stage $train_stage"

# now start preprocessing with KALDI scripts

if [ $stage -le 0 ]; then

    # remove old lang dir if it exists
    rm -rf data/lang

fi


if [ $stage -le 1 ]; then

    echo
    echo Prepare phoneme data for Kaldi
    echo

    # utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang
    utils/prepare_lang.sh data/local/dict "nspc" data/local/lang data/lang

fi

if [ $stage -le 2 ]; then
    echo
    echo make mfcc
    echo

    for datadir in train test; do
        utils/fix_data_dir.sh data/$datadir 
        steps/make_mfcc.sh --cmd "$train_cmd" --nj $nJobs data/$datadir exp/make_mfcc_chain/$datadir $mfccdir || exit 1;
        utils/fix_data_dir.sh data/${datadir} # some files fail to get mfcc for many reasons
        steps/compute_cmvn_stats.sh data/${datadir} exp/make_mfcc_chain/$datadir $mfccdir || exit 1;
        utils/fix_data_dir.sh data/${datadir} # some files fail to get mfcc for many reasons
    done
fi

if [ $stage -le 3 ]; then
    echo
    echo mono0a_chain
    echo

    steps/train_mono.sh --nj $nJobs --cmd "$train_cmd" \
      data/train data/lang exp/mono0a_chain || exit 1;
fi

if [ $stage -le 4 ]; then
    echo
    echo tri1_chain
    echo

    steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
      data/train data/lang exp/mono0a_chain exp/mono0a_ali_chain || exit 1;

    steps/train_deltas.sh --cmd "$train_cmd" 2000 10000 \
      data/train data/lang exp/mono0a_ali_chain exp/tri1_chain || exit 1;
fi

if [ $stage -le 5 ]; then
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
fi

gmm_dir=exp/$gmm
ali_dir=exp/${gmm}_ali_${train_set}_sp_comb
tree_dir=exp/nnet3${nnet3_affix}/tree_sp
lang=data/lang_chain
lat_dir=exp/nnet3${nnet3_affix}/${gmm}_${train_set}_sp_comb_lats
dir=exp/nnet3${nnet3_affix}/tdnn_sp
train_data_dir=data/${train_set}_sp_hires_comb
lores_train_data_dir=data/${train_set}_sp_comb
train_ivector_dir=exp/nnet3${nnet3_affix}/ivectors_${train_set}_sp_hires_comb

if [ $stage -le 6 ]; then
    echo
    echo run_ivector_common.sh
    echo

    local/nnet3/run_ivector_common.sh --stage $stage \
                                      --nj $nJobs \
                                      --min-seg-len $min_seg_len \
                                      --train-set $train_set \
                                      --gmm $gmm \
                                      --num-threads-ubm $num_threads_ubm \
                                      --nnet3-affix "$nnet3_affix"

    for f in $gmm_dir/final.mdl $train_data_dir/feats.scp $train_ivector_dir/ivector_online.scp \
        $lores_train_data_dir/feats.scp $ali_dir/ali.1.gz; do
      [ ! -f $f ] && echo "$0: expected file $f to exist" && exit 1
    done
fi

if [ $stage -le 7 ]; then
    echo
    echo creating lang directory with one state per phone.
    echo

    if [ -d data/lang_chain ]; then
      if [ data/lang_chain/L.fst -nt data/lang/L.fst ]; then
        echo "$0: data/lang_chain already exists, not overwriting it; continuing"
      else
        echo "$0: data/lang_chain already exists and seems to be older than data/lang..."
        echo " ... not sure what to do.  Exiting."
        exit 1;
      fi
    else
      cp -r data/lang data/lang_chain
      silphonelist=$(cat data/lang_chain/phones/silence.csl) || exit 1;
      nonsilphonelist=$(cat data/lang_chain/phones/nonsilence.csl) || exit 1;
      # Use our special topology... note that later on may have to tune this
      # topology.
      steps/nnet3/chain/gen_topo.py $nonsilphonelist $silphonelist >data/lang_chain/topo
    fi
fi

if [ $stage -le 8 ]; then
    echo
    echo 'Get the alignments as lattices (gives the chain training more freedom).'
    echo

    steps/align_fmllr_lats.sh --nj $nJobs --cmd "$train_cmd" ${lores_train_data_dir} \
        data/lang $gmm_dir $lat_dir
    rm $lat_dir/fsts.*.gz # save space
fi

if [ $stage -le 9 ]; then
    echo
    echo 'Build a tree using our new topology.  We know we have alignments for the'
    echo 'speed-perturbed data (local/nnet3/run_ivector_common.sh made them), so use'
    echo 'those.'
    echo

    if [ -f $tree_dir/final.mdl ]; then
      echo "$0: $tree_dir/final.mdl already exists, refusing to overwrite it."
      exit 1;
    fi
    steps/nnet3/chain/build_tree.sh --frame-subsampling-factor 3 \
        --context-opts "--context-width=2 --central-position=1" \
        --cmd "$train_cmd" 4000 ${lores_train_data_dir} data/lang_chain $ali_dir $tree_dir
    # FIXME: 7000 leafs

    mkdir -p $dir

    echo
    echo "$0: creating neural net configs using the xconfig parser";
    echo

    num_targets=$(tree-info $tree_dir/tree |grep num-pdfs|awk '{print $2}')
    learning_rate_factor=$(echo "print 0.5/$xent_regularize" | python)

    mkdir -p $dir/configs
    cat <<EOF > $dir/configs/network.xconfig
input dim=100 name=ivector
input dim=40 name=input

# please note that it is important to have input layer with the name=input
# as the layer immediately preceding the fixed-affine-layer to enable
# the use of short notation for the descriptor
fixed-affine-layer name=lda input=Append(-1,0,1,ReplaceIndex(ivector, t, 0)) affine-transform-file=$dir/configs/lda.mat

# the first splicing is moved before the lda layer, so no splicing here
relu-batchnorm-layer name=tdnn1 dim=450 self-repair-scale=1.0e-04
relu-batchnorm-layer name=tdnn2 input=Append(-1,0,1) dim=450
relu-batchnorm-layer name=tdnn3 input=Append(-1,0,1,2) dim=450
relu-batchnorm-layer name=tdnn4 input=Append(-3,0,3) dim=450
relu-batchnorm-layer name=tdnn5 input=Append(-3,0,3) dim=450
relu-batchnorm-layer name=tdnn6 input=Append(-6,-3,0) dim=450

## adding the layers for chain branch
relu-batchnorm-layer name=prefinal-chain input=tdnn6 dim=450 target-rms=0.5
output-layer name=output include-log-softmax=false dim=$num_targets max-change=1.5

# adding the layers for xent branch
# This block prints the configs for a separate output that will be
# trained with a cross-entropy objective in the 'chain' models... this
# has the effect of regularizing the hidden parts of the model.  we use
# 0.5 / args.xent_regularize as the learning rate factor- the factor of
# 0.5 / args.xent_regularize is suitable as it means the xent
# final-layer learns at a rate independent of the regularization
# constant; and the 0.5 was tuned so as to make the relative progress
# similar in the xent and regular final layers.
relu-batchnorm-layer name=prefinal-xent input=tdnn6 dim=450 target-rms=0.5
output-layer name=output-xent dim=$num_targets learning-rate-factor=$learning_rate_factor max-change=1.5

EOF
    steps/nnet3/xconfig_to_configs.py --xconfig-file $dir/configs/network.xconfig --config-dir $dir/configs/

fi

if [ $stage -le 10 ]; then

    echo
    echo train.py 
    echo

    steps/nnet3/chain/train.py --stage $train_stage \
      --cmd "$decode_cmd" \
      --feat.online-ivector-dir $train_ivector_dir \
      --feat.cmvn-opts "--norm-means=false --norm-vars=false" \
      --chain.xent-regularize 0.1 \
      --chain.leaky-hmm-coefficient 0.1 \
      --chain.l2-regularize 0.00005 \
      --chain.apply-deriv-weights false \
      --chain.lm-opts="--num-extra-lm-states=2000" \
      --egs.dir "$common_egs_dir" \
      --egs.opts "--frames-overlap-per-eg 0" \
      --egs.chunk-width 150 \
      --trainer.num-chunk-per-minibatch 256 \
      --trainer.frames-per-iter 1500000 \
      --trainer.num-epochs 4 \
      --trainer.optimization.proportional-shrink 20 \
      --trainer.optimization.num-jobs-initial 1 \
      --trainer.optimization.num-jobs-final 1 \
      --trainer.optimization.initial-effective-lrate 0.001 \
      --trainer.optimization.final-effective-lrate 0.0001 \
      --trainer.max-param-change 2.0 \
      --cleanup.remove-egs true \
      --feat-dir $train_data_dir \
      --tree-dir $tree_dir \
      --lat-dir $lat_dir \
      --dir $dir
fi

if [ $stage -le 11 ]; then
    echo
    echo mkgraph
    echo

    utils/mkgraph.sh --self-loop-scale 1.0 data/lang_test $dir $dir/graph
fi

if [ $stage -le 12 ]; then
    echo
    echo decode
    echo

    steps/nnet3/decode.sh --num-threads 1 --nj $nDecodeJobs --cmd "$decode_cmd" \
                          --acwt 1.0 --post-decode-acwt 10.0 \
                          --online-ivector-dir exp/nnet3${nnet3_affix}/ivectors_test_hires \
                          --scoring-opts "--min-lmwt 5 " \
                          $dir/graph data/test_hires $dir/decode_test || exit 1;

    grep WER $dir/decode_test/scoring_kaldi/best_wer >>RESULTS.txt
fi

#
# smaller model for embedded use
#

if [ $stage -le 13 ]; then

    dir=exp/nnet3${nnet3_affix}/tdnn_250

    mkdir -p $dir

    echo
    echo "$0: creating neural net configs using the xconfig parser";
    echo

    num_targets=$(tree-info $tree_dir/tree |grep num-pdfs|awk '{print $2}')
    learning_rate_factor=$(echo "print 0.5/$xent_regularize" | python)

    mkdir -p $dir/configs
    cat <<EOF > $dir/configs/network.xconfig
input dim=100 name=ivector
input dim=40 name=input

# please note that it is important to have input layer with the name=input
# as the layer immediately preceding the fixed-affine-layer to enable
# the use of short notation for the descriptor
fixed-affine-layer name=lda input=Append(-1,0,1,ReplaceIndex(ivector, t, 0)) affine-transform-file=$dir/configs/lda.mat

# the first splicing is moved before the lda layer, so no splicing here
relu-batchnorm-layer name=tdnn1 dim=250 self-repair-scale=1.0e-04
relu-batchnorm-layer name=tdnn2 input=Append(-1,0,1) dim=250
relu-batchnorm-layer name=tdnn3 input=Append(-1,0,1,2) dim=250
relu-batchnorm-layer name=tdnn4 input=Append(-3,0,3) dim=250
relu-batchnorm-layer name=tdnn5 input=Append(-3,0,3) dim=250
relu-batchnorm-layer name=tdnn6 input=Append(-6,-3,0) dim=250

## adding the layers for chain branch
relu-batchnorm-layer name=prefinal-chain input=tdnn6 dim=250 target-rms=0.5
output-layer name=output include-log-softmax=false dim=$num_targets max-change=1.5

# adding the layers for xent branch
# This block prints the configs for a separate output that will be
# trained with a cross-entropy objective in the 'chain' models... this
# has the effect of regularizing the hidden parts of the model.  we use
# 0.5 / args.xent_regularize as the learning rate factor- the factor of
# 0.5 / args.xent_regularize is suitable as it means the xent
# final-layer learns at a rate independent of the regularization
# constant; and the 0.5 was tuned so as to make the relative progress
# similar in the xent and regular final layers.
relu-batchnorm-layer name=prefinal-xent input=tdnn6 dim=250 target-rms=0.5
output-layer name=output-xent dim=$num_targets learning-rate-factor=$learning_rate_factor max-change=1.5

EOF
    steps/nnet3/xconfig_to_configs.py --xconfig-file $dir/configs/network.xconfig --config-dir $dir/configs/

    echo
    echo train.py 
    echo

    steps/nnet3/chain/train.py --stage $train_stage \
      --cmd "$decode_cmd" \
      --feat.online-ivector-dir $train_ivector_dir \
      --feat.cmvn-opts "--norm-means=false --norm-vars=false" \
      --chain.xent-regularize 0.1 \
      --chain.leaky-hmm-coefficient 0.1 \
      --chain.l2-regularize 0.00005 \
      --chain.apply-deriv-weights false \
      --chain.lm-opts="--num-extra-lm-states=2000" \
      --egs.dir "$common_egs_dir" \
      --egs.opts "--frames-overlap-per-eg 0" \
      --egs.chunk-width 150 \
      --trainer.num-chunk-per-minibatch 512 \
      --trainer.frames-per-iter 1500000 \
      --trainer.num-epochs 4 \
      --trainer.optimization.proportional-shrink 20 \
      --trainer.optimization.num-jobs-initial 1 \
      --trainer.optimization.num-jobs-final 1 \
      --trainer.optimization.initial-effective-lrate 0.001 \
      --trainer.optimization.final-effective-lrate 0.0001 \
      --trainer.max-param-change 2.0 \
      --cleanup.remove-egs true \
      --feat-dir $train_data_dir \
      --tree-dir $tree_dir \
      --lat-dir $lat_dir \
      --dir $dir

    echo
    echo mkgraph
    echo

    utils/mkgraph.sh --self-loop-scale 1.0 data/lang_test $dir $dir/graph

    echo
    echo decode
    echo

    steps/nnet3/decode.sh --num-threads 1 --nj $nDecodeJobs --cmd "$decode_cmd" \
                          --acwt 1.0 --post-decode-acwt 10.0 \
                          --online-ivector-dir exp/nnet3${nnet3_affix}/ivectors_test_hires \
                          --scoring-opts "--min-lmwt 5 " \
                          $dir/graph data/test_hires $dir/decode_test || exit 1;

    grep WER $dir/decode_test/scoring_kaldi/best_wer >>RESULTS.txt

fi

#
# larger tdnn_f model for higher end machines
#
# network config based on 
# egs/swbd/s5c/local/chain/tuning/run_tdnn_7q.sh
#

dir=exp/nnet3${nnet3_affix}/tdnn_f

num_targets=$(tree-info $tree_dir/tree |grep num-pdfs|awk '{print $2}')
learning_rate_factor=$(echo "print 0.5/$xent_regularize" | python)
affine_opts="l2-regularize=0.01 dropout-proportion=0.0 dropout-per-dim=true dropout-per-dim-continuous=true"
tdnnf_opts="l2-regularize=0.01 dropout-proportion=0.0 bypass-scale=0.66"
linear_opts="l2-regularize=0.01 orthonormal-constraint=-1.0"
prefinal_opts="l2-regularize=0.01"
output_opts="l2-regularize=0.002"

if [ $stage -le 14 ]; then

    mkdir -p $dir

    echo
    echo "$0: creating neural net configs using the xconfig parser";
    echo

    mkdir -p $dir/configs
    cat <<EOF > $dir/configs/network.xconfig
input dim=100 name=ivector
input dim=40 name=input

# please note that it is important to have input layer with the name=input
# as the layer immediately preceding the fixed-affine-layer to enable
# the use of short notation for the descriptor
fixed-affine-layer name=lda input=Append(-1,0,1,ReplaceIndex(ivector, t, 0)) affine-transform-file=$dir/configs/lda.mat

# the first splicing is moved before the lda layer, so no splicing here
relu-batchnorm-dropout-layer name=tdnn1 $affine_opts dim=1536
tdnnf-layer name=tdnnf2 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=1
tdnnf-layer name=tdnnf3 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=1
tdnnf-layer name=tdnnf4 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=1
tdnnf-layer name=tdnnf5 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=0
tdnnf-layer name=tdnnf6 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf7 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf8 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf9 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf10 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf11 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf12 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf13 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf14 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
tdnnf-layer name=tdnnf15 $tdnnf_opts dim=1536 bottleneck-dim=160 time-stride=3
linear-component name=prefinal-l dim=256 $linear_opts

prefinal-layer name=prefinal-chain input=prefinal-l $prefinal_opts big-dim=1536 small-dim=256
output-layer name=output include-log-softmax=false dim=$num_targets $output_opts

prefinal-layer name=prefinal-xent input=prefinal-l $prefinal_opts big-dim=1536 small-dim=256
output-layer name=output-xent dim=$num_targets learning-rate-factor=$learning_rate_factor $output_opts

EOF
    steps/nnet3/xconfig_to_configs.py --xconfig-file $dir/configs/network.xconfig --config-dir $dir/configs/

fi

if [ $stage -le 15 ]; then

    echo
    echo train.py 
    echo

    steps/nnet3/chain/train.py --stage $train_stage \
      --cmd "$decode_cmd" \
      --feat.online-ivector-dir $train_ivector_dir \
      --feat.cmvn-opts "--norm-means=false --norm-vars=false" \
      --chain.xent-regularize $xent_regularize \
      --chain.leaky-hmm-coefficient 0.1 \
      --chain.l2-regularize 0.0 \
      --chain.apply-deriv-weights false \
      --chain.lm-opts="--num-extra-lm-states=2000" \
      --trainer.dropout-schedule $dropout_schedule \
      --trainer.add-option="--optimization.memory-compression-level=2" \
      --egs.dir "$common_egs_dir" \
      --egs.stage $get_egs_stage \
      --egs.opts "--frames-overlap-per-eg 0 --constrained false" \
      --egs.chunk-width $frames_per_eg \
      --trainer.num-chunk-per-minibatch 288 \
      --trainer.frames-per-iter 1500000 \
      --trainer.num-epochs 6 \
      --trainer.optimization.num-jobs-initial 1 \
      --trainer.optimization.num-jobs-final 1 \
      --trainer.optimization.initial-effective-lrate 0.00025 \
      --trainer.optimization.final-effective-lrate 0.000025 \
      --trainer.max-param-change 2.0 \
      --use-gpu wait \
      --cleanup.remove-egs true \
      --feat-dir $train_data_dir \
      --tree-dir $tree_dir \
      --lat-dir $lat_dir \
      --dir $dir  || exit 1;

    echo
    echo mkgraph
    echo

    utils/mkgraph.sh --self-loop-scale 1.0 data/lang_test $dir $dir/graph

    echo
    echo decode
    echo

    steps/nnet3/decode.sh --num-threads 1 --nj $nDecodeJobs --cmd "$decode_cmd" \
                          --acwt 1.0 --post-decode-acwt 10.0 \
                          --online-ivector-dir exp/nnet3${nnet3_affix}/ivectors_test_hires \
                          --scoring-opts "--min-lmwt 5 " \
                          $dir/graph data/test_hires $dir/decode_test || exit 1;

    grep WER $dir/decode_test/scoring_kaldi/best_wer >>RESULTS.txt

fi

