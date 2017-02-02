#!/bin/bash

# Copyright 2016 G. Bartsch
# Copyright 2015 Language Technology, Technische Universitaet Darmstadt (author: Benjamin Milde)
# Copyright 2014 QCRI (author: Ahmed Ali)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# adapted from kaldi-tuda-de run.sh
# adapted from wsj's run.sh

mfccdir=mfcc

# remove old lang dir if it exists
rm -rf data/lang

# now start preprocessing with KALDI scripts

if [ -f cmd.sh ]; then
      . cmd.sh; else
         echo "missing cmd.sh"; exit 1;
fi

#Path also sets LC_ALL=C for Kaldi, otherwise you will experience strange (and hard to debug!) bugs. It should be set here, after the python scripts and not at the beginning of this script
if [ -f path.sh ]; then
      . path.sh; else
         echo "missing path.sh"; exit 1;

fi

echo "Runtime configuration is: nJobs $nJobs, nDecodeJobs $nDecodeJobs. If this is not what you want, edit cmd.sh"

#Make sure that LC_ALL is C for Kaldi, otherwise you will experience strange (and hard to debug!) bugs
export LC_ALL=C

#Prepare phoneme data for Kaldi
utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang

# Now make MFCC features.
for x in train dev test ; do
    utils/fix_data_dir.sh data/$x # some files fail to get mfcc for many reasons
    steps/make_mfcc.sh --cmd "$train_cmd" --nj $nJobs data/$x exp/make_mfcc/$x $mfccdir
    utils/fix_data_dir.sh data/$x # some files fail to get mfcc for many reasons
    steps/compute_cmvn_stats.sh data/$x exp/make_mfcc/$x $mfccdir
    utils/fix_data_dir.sh data/$x
done

# prepare LM
local/build_lm.sh

# Here we start the AM

#local/run_am.sh
#local/run_dnn.sh

testDir=test

#
# mono, mono_ali, tri1
#

# Train monophone models (right now makes no sense to do it only on a subset)
# Note: the --boost-silence option should probably be omitted by default
steps/train_mono.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/mono || exit 1;

# Get alignments from monophone system.
steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/mono exp/mono_ali || exit 1;

# train tri1 [first triphone pass]
# FIXME: steps/train_deltas.sh --cmd "$train_cmd" \
# FIXME:   2500 30000 data/train data/lang exp/mono_ali exp/tri1 || exit 1;
steps/train_deltas.sh --cmd "$train_cmd" 2000 10000 \
  data/train data/lang exp/mono_ali exp/tri1 || exit 1;

#
# train and decode tri2b [LDA+MLLT]
#

steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/tri1 exp/tri1_ali || exit 1;

# FIXME: steps/train_lda_mllt.sh --cmd "$train_cmd" 4000 50000 \
# FIXME:   data/train data/lang exp/tri1_ali exp/tri2b || exit 1;
steps/train_lda_mllt.sh --cmd "$train_cmd" \
  --splice-opts "--left-context=3 --right-context=3" 2500 15000 \
  data/train data/lang exp/tri1_ali exp/tri2b 

time utils/mkgraph.sh data/lang_test exp/tri2b exp/tri2b/graph || exit 1;
time steps/decode.sh --nj $nDecodeJobs --cmd "$decode_cmd" exp/tri2b/graph data/$testDir exp/tri2b/decode

#
# tri2b_mmi Do MMI on top of LDA+MLLT.
#

# Align all data with LDA+MLLT system (tri2b)
steps/align_si.sh --nj $nJobs --cmd "$train_cmd" \
  --use-graphs true data/train data/lang exp/tri2b exp/tri2b_ali  || exit 1;

#  Do MMI on top of LDA+MLLT.
steps/make_denlats.sh --nj $nJobs --cmd "$train_cmd" \
 data/train data/lang exp/tri2b exp/tri2b_denlats || exit 1;
steps/train_mmi.sh --cmd "$train_cmd" data/train data/lang exp/tri2b_ali \
 exp/tri2b_denlats exp/tri2b_mmi || exit 1;

time steps/decode.sh  --nj $nDecodeJobs --cmd "$decode_cmd"  exp/tri2b/graph data/$testDir exp/tri2b_mmi/decode

steps/train_mmi.sh --cmd "$train_cmd" --boost 0.05 data/train data/lang exp/tri2b_ali \
 exp/tri2b_denlats exp/tri2b_mmi_b0.05 || exit 1;

time steps/decode.sh  --nj $nDecodeJobs --cmd "$decode_cmd" exp/tri2b/graph data/$testDir exp/tri2b_mmi_b0.05/decode || exit 1;

#
# tri2b_mpe Do MPE.
#

steps/train_mpe.sh --cmd "$train_cmd" data/train data/lang exp/tri2b_ali exp/tri2b_denlats exp/tri2b_mpe || exit 1;

time steps/decode.sh --nj $nDecodeJobs --cmd "$decode_cmd" exp/tri2b/graph data/$testDir exp/tri2b_mpe/decode || exit 1;

#
# tri3b From 2b system, train 3b which is LDA + MLLT + SAT.
#

steps/train_sat.sh --cmd "$train_cmd" \
  4200 40000 data/train data/lang exp/tri2b_ali exp/tri3b || exit 1;
utils/mkgraph.sh data/lang_test exp/tri3b exp/tri3b/graph|| exit 1;
time steps/decode_fmllr.sh --nj $nDecodeJobs --cmd "$decode_cmd" exp/tri3b/graph data/$testDir exp/tri3b/decode || exit 1;

#
# tri3b_mmi Do MMI on top of LDA+MLLT+SAT.
#

# From 3b system, align all data.
steps/align_fmllr.sh --nj $nJobs --cmd "$train_cmd" \
  data/train data/lang exp/tri3b exp/tri3b_ali || exit 1;

#  Do MMI on top of LDA+MLLT+SAT.
steps/make_denlats.sh --nj $nJobs --cmd "$train_cmd" \
 --transform-dir exp/tri3b data/train data/lang exp/tri3b exp/tri3b_denlats || exit 1;

steps/train_mmi.sh --cmd "$train_cmd" data/train data/lang exp/tri3b_ali \
 exp/tri3b_denlats exp/tri3b_mmi || exit 1;

time steps/decode.sh  --iter 4 --nj $nDecodeJobs --cmd "$decode_cmd"  exp/tri3b/graph data/$testDir exp/tri3b_mmi/decode

steps/train_mmi.sh --cmd "$train_cmd" --boost 0.05 data/train data/lang exp/tri3b_ali \
 exp/tri3b_denlats exp/tri3b_mmi_b0.05 || exit 1;

time steps/decode.sh  --nj $nDecodeJobs --cmd "$decode_cmd" exp/tri3b/graph data/$testDir exp/tri3b_mmi_b0.05/decode || exit 1;

#
# tri3b_mpe Do MPE.
#

steps/train_mpe.sh --cmd "$train_cmd" data/train data/lang exp/tri3b_ali exp/tri3b_denlats exp/tri3b_mpe || exit 1;

time steps/decode.sh  --nj $nDecodeJobs --cmd "$decode_cmd" exp/tri3b/graph data/$testDir exp/tri3b_mpe/decode || exit 1;



# ## SGMM (subspace gaussian mixture model), excluding the "speaker-dependent weights"
#
# FIXME: disabled since it seems to fail for now
#
# steps/train_ubm.sh --cmd "$train_cmd" 700 \
#  data/train data/lang exp/tri3b_ali exp/ubm5a || exit 1;
# 
# steps/train_sgmm2.sh --cmd "$train_cmd" 5000 20000 data/train data/lang exp/tri3b_ali \
#   exp/ubm5a/final.ubm exp/sgmm_5a || exit 1;
# 
# utils/mkgraph.sh data/lang_test exp/sgmm_5a exp/sgmm_5a/graph || exit 1;
# 
# steps/decode_sgmm2.sh --nj $nDecodeJobs --cmd "$decode_cmd" --config conf/decode.config \
#   --transform-dir exp/tri3b/decode exp/sgmm_5a/graph data/$testDir exp/sgmm_5a/decode
# 
# steps/align_sgmm2.sh --nj $nJobs --cmd "$train_cmd" --transform-dir exp/tri3b_ali \
#   --use-graphs true --use-gselect true data/train data/lang exp/sgmm_5a exp/sgmm_5a_ali || exit 1;
# 
# ## boosted MMI on SGMM
# steps/make_denlats_sgmm2.sh --nj $nJobs --sub-split 30 --beam 9.0 --lattice-beam 6 \
#   --cmd "$decode_cmd" --transform-dir \
#   exp/tri3b_ali data/train data/lang exp/sgmm_5a_ali exp/sgmm_5a_denlats || exit 1;
# 
# steps/train_mmi_sgmm2.sh --cmd "$train_cmd" --num-iters 8 --transform-dir exp/tri3b_ali --boost 0.1 \
#   data/train data/lang exp/sgmm_5a exp/sgmm_5a_denlats exp/sgmm_5a_mmi_b0.1
# 
# #decode GMM MMI
# utils/mkgraph.sh data/lang_test exp/sgmm_5a_mmi_b0.1 exp/sgmm_5a_mmi_b0.1/graph || exit 1;
# 
# steps/decode_sgmm2.sh --nj $nDecodeJobs --cmd "$decode_cmd" --config conf/decode.config \
#   --transform-dir exp/tri3b/decode exp/sgmm_5a_mmi_b0.1/graph data/$testDir exp/sgmm_5a_mmi_b0.1/decode
# 
# for n in 1 2 3 4; do
#   steps/decode_sgmm2_rescore.sh --cmd "$decode_cmd" --iter $n --transform-dir exp/tri3b/decode data/lang_test \
#     data/$testDir exp/sgmm_5a_mmi_b0.1/decode exp/sgmm_5a_mmi_b0.1/decode$n
# 
#   steps/decode_sgmm_rescore.sh --cmd "$decode_cmd" --iter $n --transform-dir exp/tri3b/decode data/lang_test \
#     data/$testDir exp/sgmm_5a/decode exp/sgmm_5a_mmi_onlyRescoreb0.1/decode$n
# done

time=$(date +"%Y-%m-%d-%H-%M-%S")
#get WER
for x in exp/*/decode*; do [ -d $x ] && grep WER $x/wer_* | utils/best_wer.sh; \
done | sort -n -r -k2 > RESULTS.txt

echo training succedded
exit 0
