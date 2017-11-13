#!/bin/bash

if [ $# != 1 ] ; then
    echo "usage: $0 <lang>"
    exit 1
fi

LANG=$1
DISTDIR=data/dist/$LANG

# rm -rf $DISTDIR
# mkdir $DISTDIR

datum=`date +%Y%m%d`

#
# kaldi chain models 
#

AMNAME="kaldi-chain-voxforge-${LANG}-r$datum"

mkdir "$DISTDIR/$AMNAME"

function export_kaldi_chain {

    EXPNAME=$1
    GRAPHNAME=$2

    mkdir "$DISTDIR/$AMNAME/$EXPNAME"

    cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/$EXPNAME/final.mdl                  $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/$EXPNAME/cmvn_opts                  $DISTDIR/$AMNAME/$EXPNAME/ 2>/dev/null 

    cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/$GRAPHNAME/HCLG.fst                 $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/$GRAPHNAME/words.txt                $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/$GRAPHNAME/num_pdfs                 $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/$GRAPHNAME/phones/align_lexicon.int $DISTDIR/$AMNAME/$EXPNAME/

}

export_kaldi_chain tdnn_sp tdnn_sp/graph
export_kaldi_chain tdnn_250 tdnn_250/graph

mkdir "$DISTDIR/$AMNAME/extractor"

cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/extractor/final.mat                  "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/extractor/global_cmvn.stats          "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/extractor/final.dubm                 "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/extractor/final.ie                   "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/extractor/splice_opts                "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3_chain/ivectors_test_hires/conf/splice.conf "$DISTDIR/$AMNAME/extractor/"

cp data/dst/speech/${LANG}/kaldi/RESULTS.txt $DISTDIR/$AMNAME/
cp README.md "$DISTDIR/$AMNAME"
cp LICENSE   "$DISTDIR/$AMNAME"
cp AUTHORS   "$DISTDIR/$AMNAME"

mkdir "$DISTDIR/$AMNAME/conf"
cp data/src/speech/kaldi-mfcc.conf        $DISTDIR/$AMNAME/conf/mfcc.conf 
cp data/src/speech/kaldi-mfcc-hires.conf  $DISTDIR/$AMNAME/conf/mfcc-hires.conf  
cp data/src/speech/kaldi-online-cmvn.conf $DISTDIR/$AMNAME/conf/online_cmvn.conf

pushd $DISTDIR
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"
popd

rm -r "$DISTDIR/$AMNAME"

#FIXME
exit 0

#
# kaldi nnet3 models 
#

AMNAME="kaldi-nnet3-voxforge-${LANG}-r$datum"

mkdir "$DISTDIR/$AMNAME"

function export_kaldi_nnet3 {

    EXPNAME=$1
    GRAPHNAME=$2

    mkdir "$DISTDIR/$AMNAME/$EXPNAME"

    cp data/dst/speech/${LANG}/kaldi/exp/nnet3/$EXPNAME/final.mdl                  $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3/$EXPNAME/cmvn_opts                  $DISTDIR/$AMNAME/$EXPNAME/ 2>/dev/null 

    cp data/dst/speech/${LANG}/kaldi/exp/nnet3/$GRAPHNAME/HCLG.fst                 $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3/$GRAPHNAME/words.txt                $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3/$GRAPHNAME/num_pdfs                 $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/${LANG}/kaldi/exp/nnet3/$GRAPHNAME/phones/align_lexicon.int $DISTDIR/$AMNAME/$EXPNAME/

}

export_kaldi_nnet3 nnet_tdnn_a  nnet_tdnn_a/graph
# export_kaldi_nnet3 lstm_ld5     lstm_ld5/graph

mkdir "$DISTDIR/$AMNAME/extractor"

cp data/dst/speech/${LANG}/kaldi/exp/nnet3/extractor/final.mat            "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3/extractor/global_cmvn.stats    "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3/extractor/final.dubm           "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3/extractor/final.ie             "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3/extractor/splice_opts          "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/${LANG}/kaldi/exp/nnet3/ivectors_test/conf/splice.conf "$DISTDIR/$AMNAME/extractor/"

cp data/dst/speech/${LANG}/kaldi/RESULTS.txt $DISTDIR/$AMNAME/
cp README.md "$DISTDIR/$AMNAME"
cp LICENSE   "$DISTDIR/$AMNAME"
cp AUTHORS   "$DISTDIR/$AMNAME"

mkdir "$DISTDIR/$AMNAME/conf"
cp data/src/speech/kaldi-mfcc.conf        $DISTDIR/$AMNAME/conf/mfcc.conf 
cp data/src/speech/kaldi-mfcc-hires.conf  $DISTDIR/$AMNAME/conf/mfcc-hires.conf  
cp data/src/speech/kaldi-online-cmvn.conf $DISTDIR/$AMNAME/conf/online_cmvn.conf

pushd $DISTDIR
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"
popd

rm -r "$DISTDIR/$AMNAME"

#
# cont sphinx model
#

AMNAME="cmusphinx-cont-voxforge-${LANG}-r$datum"

mkdir "$DISTDIR/$AMNAME"
mkdir "$DISTDIR/$AMNAME/model_parameters"

cp -r data/dst/speech/${LANG}/cmusphinx_cont/model_parameters/voxforge.cd_cont_6000 "$DISTDIR/$AMNAME/model_parameters"
cp -r data/dst/speech/${LANG}/cmusphinx_cont/etc "$DISTDIR/$AMNAME"
cp data/dst/speech/${LANG}/cmusphinx_cont/voxforge.html "$DISTDIR/$AMNAME"
cp README.md "$DISTDIR/$AMNAME"
cp LICENSE   "$DISTDIR/$AMNAME"
cp AUTHORS   "$DISTDIR/$AMNAME"

pushd $DISTDIR
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"
popd

rm -r "$DISTDIR/$AMNAME"

#
# ptm sphinx model
#

AMNAME="cmusphinx-ptm-voxforge-${LANG}-r$datum"

mkdir "$DISTDIR/$AMNAME"
mkdir "$DISTDIR/$AMNAME/model_parameters"

cp -r data/dst/speech/${LANG}/cmusphinx_ptm/model_parameters/voxforge.cd_ptm_5000 "$DISTDIR/$AMNAME/model_parameters"
cp -r data/dst/speech/${LANG}/cmusphinx_ptm/etc "$DISTDIR/$AMNAME"
cp data/dst/speech/${LANG}/cmusphinx_ptm/voxforge.html "$DISTDIR/$AMNAME"
cp README.md "$DISTDIR/$AMNAME"
cp LICENSE   "$DISTDIR/$AMNAME"
cp AUTHORS   "$DISTDIR/$AMNAME"

pushd $DISTDIR
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"
popd

rm -r "$DISTDIR/$AMNAME"

#
# srilm
#

LMNAME="srilm-voxforge-${LANG}-r$datum.arpa"
cp data/dst/speech/${LANG}/srilm/lm.arpa ${DISTDIR}/$LMNAME
gzip ${DISTDIR}/$LMNAME

# 
# cmuclmtk
#

# LMNAME="cmuclmtk-voxforge-${LANG}-r$datum.arpa"
# cp data/dst/speech/${LANG}/cmusphinx_cont/voxforge.arpa $DISTDIR/$LMNAME
# gzip $DISTDIR/$LMNAME

#
# sequitur
#

MODELNAME="sequitur-voxforge-${LANG}-r$datum"
cp data/dst/speech/${LANG}/sequitur/model-6 $DISTDIR/$MODELNAME
gzip $DISTDIR/$MODELNAME

#
# copyright info
#

cp README.md "$DISTDIR"
cp LICENSE   "$DISTDIR"
cp AUTHORS   "$DISTDIR"

#
# upload
#

echo rsync -avPz --delete --bwlimit=256 data/dist/${LANG} goofy:/var/www/html/voxforge/

