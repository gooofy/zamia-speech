#!/bin/bash

DISTDIR=data/dist

rm -rf $DISTDIR
mkdir $DISTDIR

datum=`date +%Y%m%d`

#
# kaldi nnet3 models de
#

AMNAME="kaldi-nnet3-voxforge-de-r$datum"

mkdir "$DISTDIR/$AMNAME"

function export_kaldi_nnet3 {

    EXPNAME=$1
    GRAPHNAME=$2

    mkdir "$DISTDIR/$AMNAME/$EXPNAME"

    cp data/dst/speech/de/kaldi/exp/nnet3/$EXPNAME/final.mdl   $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/nnet3/$EXPNAME/cmvn_opts   $DISTDIR/$AMNAME/$EXPNAME/          2>/dev/null 

    cp data/dst/speech/de/kaldi/exp/nnet3/$GRAPHNAME/HCLG.fst  $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/nnet3/$GRAPHNAME/words.txt $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/nnet3/$GRAPHNAME/num_pdfs  $DISTDIR/$AMNAME/$EXPNAME/

}

export_kaldi_nnet3 nnet_tdnn_a  nnet_tdnn_a/graph
export_kaldi_nnet3 lstm_ld5     lstm_ld5/graph

mkdir "$DISTDIR/$AMNAME/extractor"

cp data/dst/speech/de/kaldi/exp/nnet3/extractor/final.mat            "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/de/kaldi/exp/nnet3/extractor/global_cmvn.stats    "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/de/kaldi/exp/nnet3/extractor/final.dubm           "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/de/kaldi/exp/nnet3/extractor/final.ie             "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/de/kaldi/exp/nnet3/extractor/splice_opts          "$DISTDIR/$AMNAME/extractor/"
cp data/dst/speech/de/kaldi/exp/nnet3/ivectors_test/conf/splice.conf "$DISTDIR/$AMNAME/extractor/"

cp data/dst/speech/de/kaldi/RESULTS.txt $DISTDIR/$AMNAME/
cp README.md "$DISTDIR/$AMNAME"
cp COPYING   "$DISTDIR/$AMNAME"
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
# kaldi gmm models de
#

AMNAME="kaldi-gmm-voxforge-de-r$datum"

mkdir "$DISTDIR/$AMNAME"

function export_kaldi_model {

    EXPNAME=$1
    GRAPHNAME=$2

    mkdir "$DISTDIR/$AMNAME/$EXPNAME"

    cp data/dst/speech/de/kaldi/exp/$EXPNAME/final.mdl   $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/$EXPNAME/final.mat   $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/$EXPNAME/splice_opts $DISTDIR/$AMNAME/$EXPNAME/          2>/dev/null
    cp data/dst/speech/de/kaldi/exp/$EXPNAME/cmvn_opts   $DISTDIR/$AMNAME/$EXPNAME/          2>/dev/null 
    cp data/dst/speech/de/kaldi/exp/$EXPNAME/delta_opts  $DISTDIR/$AMNAME/$EXPNAME/          2>/dev/null 

    cp data/dst/speech/de/kaldi/exp/$GRAPHNAME/HCLG.fst  $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/$GRAPHNAME/words.txt $DISTDIR/$AMNAME/$EXPNAME/
    cp data/dst/speech/de/kaldi/exp/$GRAPHNAME/num_pdfs  $DISTDIR/$AMNAME/$EXPNAME/

}

# export_kaldi_model tri2b           tri2b/graph
export_kaldi_model tri2b_mmi       tri2b_denlats/dengraph
export_kaldi_model tri2b_mmi_b0.05 tri2b_denlats/dengraph
export_kaldi_model tri2b_mpe       tri2b_denlats/dengraph
# export_kaldi_model tri3b           tri3b/graph
export_kaldi_model tri3b_mpe       tri3b_denlats/dengraph
export_kaldi_model tri3b_mmi       tri3b_denlats/dengraph
export_kaldi_model tri3b_mmi_b0.05 tri3b_denlats/dengraph

cp data/dst/speech/de/kaldi/RESULTS.txt $DISTDIR/$AMNAME/
cp README.md "$DISTDIR/$AMNAME"
cp COPYING   "$DISTDIR/$AMNAME"
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
# cont sphinx model de
#

AMNAME="cmusphinx-cont-voxforge-de-r$datum"

mkdir "$DISTDIR/$AMNAME"
mkdir "$DISTDIR/$AMNAME/model_parameters"

cp -r data/dst/speech/de/cmusphinx_cont/model_parameters/voxforge.cd_cont_6000 "$DISTDIR/$AMNAME/model_parameters"
cp -r data/dst/speech/de/cmusphinx_cont/etc "$DISTDIR/$AMNAME"
cp data/dst/speech/de/cmusphinx_cont/voxforge.html "$DISTDIR/$AMNAME"
cp README.md "$DISTDIR/$AMNAME"
cp COPYING   "$DISTDIR/$AMNAME"
cp AUTHORS   "$DISTDIR/$AMNAME"

pushd $DISTDIR
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"
popd

rm -r "$DISTDIR/$AMNAME"

#
# ptm sphinx model de
#

AMNAME="cmusphinx-ptm-voxforge-de-r$datum"

mkdir "$DISTDIR/$AMNAME"
mkdir "$DISTDIR/$AMNAME/model_parameters"

cp -r data/dst/speech/de/cmusphinx_ptm/model_parameters/voxforge.cd_ptm_5000 "$DISTDIR/$AMNAME/model_parameters"
cp -r data/dst/speech/de/cmusphinx_ptm/etc "$DISTDIR/$AMNAME"
cp data/dst/speech/de/cmusphinx_ptm/voxforge.html "$DISTDIR/$AMNAME"
cp README.md "$DISTDIR/$AMNAME"
cp COPYING   "$DISTDIR/$AMNAME"
cp AUTHORS   "$DISTDIR/$AMNAME"

pushd $DISTDIR
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"
popd

rm -r "$DISTDIR/$AMNAME"

#
# srilm de
#

LMNAME="srilm-voxforge-de-r$datum.arpa"
cp data/dst/speech/de/kaldi/data/local/lm/lm.arpa data/dist/$LMNAME
gzip data/dist/$LMNAME

# 
# cmuclmtk de
#

LMNAME="cmuclmtk-voxforge-de-r$datum.arpa"
cp data/dst/speech/de/cmusphinx_cont/voxforge.arpa $DISTDIR/$LMNAME
gzip $DISTDIR/$LMNAME

#
# sequitur de
#

MODELNAME="sequitur-voxforge-de-r$datum"
cp data/dst/speech/de/sequitur/model-6 $DISTDIR/$MODELNAME
gzip $DISTDIR/$MODELNAME

#
# copyright info
#

cp README.md "$DISTDIR"
cp COPYING   "$DISTDIR"
cp AUTHORS   "$DISTDIR"

#
# upload
#

echo rsync -avPz --delete --bwlimit=256 data/dist goofy:/var/www/html/voxforge/de

