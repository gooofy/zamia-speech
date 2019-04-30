#!/bin/bash

#
# Copyright 2019 Guenter Bartsch
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

#
# adapt trained kaldi model to other LM, re-run decode on adapted model
#


stage=0
nnet3_affix=_chain  # cleanup affix for nnet3 and chain dirs, e.g. _cleaned

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

if [ $# != 2 ] ; then
    echo "usage $0 <lm_target> <exp_target>"
    exit 1
fi

# lm_target="srilm"
# lm_target="lm_medium"
lm_target=$1
exp_target=$2

lmdir=data/local/lm_target
lang=data/lang_test_target

if [ $stage -le 1 ]; then
    rm -rf ${lang}
    cp -r data/lang ${lang}

    rm -rf ${lmdir}
    cp -r data/local/lm ${lmdir}
fi 

if [ $stage -le 2 ]; then
    echo
    echo "creating target G.fst..."

    cat ${lm_target}/lm.arpa | utils/find_arpa_oovs.pl $lang/words.txt  > $lmdir/oovs_lm.txt

    cat ${lm_target}/lm.arpa | \
        grep -v '<s> <s>' | \
        grep -v '</s> <s>' | \
        grep -v '</s> </s>' | \
        arpa2fst - | fstprint | \
        utils/remove_oovs.pl $lmdir/oovs_lm.txt | \
        utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$lang/words.txt \
          --osymbols=$lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
         fstrmepsilon > $lang/G.fst
fi

dir=exp/nnet3${nnet3_affix}/${exp_target}

if [ $stage -le 3 ]; then

    rm -rf $dir
    mkdir -p $dir

    for F in accuracy.report cmvn_opts configs den.fst final.ie.id final.mdl frame_subsampling_factor init.raw lda.mat lda_stats normalization.fst phone_lm.fst phones.txt srand tree ; do
        cp -r exp/nnet3${nnet3_affix}/tdnn_f/$F   $dir/
    done

    echo
    echo "mkgraph for ${lm_target} ${exp_target}"
    echo

    time utils/mkgraph.sh --self-loop-scale 1.0 $lang $dir $dir/graph

fi

if [ $stage -le 4 ]; then
    echo
    echo "decode for ${exp_target}"
    echo

    time steps/nnet3/decode.sh --num-threads 1 --nj $nDecodeJobs --cmd "$decode_cmd" \
                               --acwt 1.0 --post-decode-acwt 10.0 \
                               --online-ivector-dir exp/nnet3${nnet3_affix}/ivectors_test_hires \
                               --scoring-opts "--min-lmwt 5 " \
                               $dir/graph data/test_hires $dir/decode_test || exit 1;

    grep WER $dir/decode_test/scoring_kaldi/best_wer >>RESULTS.txt

fi

