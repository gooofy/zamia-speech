#!/bin/bash

if [ $# -lt 2 ] ; then
    echo "usage: $0 <model> [kaldi <experiment>|sphinx_cont|sphinx_ptm|sequitur|srilm]"
    exit 1
fi

MODEL=$1
WHAT=$2

datum=`date +%Y%m%d`

if [ $WHAT = "kaldi" ] ; then

    if [ $# != 3 ] ; then
        echo "usage: $0 <model> [kaldi <experiment>|sphinx_cont|sphinx_ptm|sequitur|srilm]"
        exit 2
    fi

    DISTDIR=data/dist/asr-models
    EXPNAME=$3

    if [ -e data/dst/asr-models/kaldi/${MODEL}/exp/nnet3_chain/${EXPNAME} ] ; then
        EXPDIR="data/dst/asr-models/kaldi/${MODEL}/exp/nnet3_chain"
    else
        EXPDIR="data/dst/asr-models/kaldi/${MODEL}/exp"
    fi

    AMNAME="kaldi-${MODEL}-${EXPNAME}-r$datum"

    echo "$AMNAME ..."

    mkdir -p "$DISTDIR/$AMNAME/model"

    cp $EXPDIR/$EXPNAME/final.mdl                             $DISTDIR/$AMNAME/model/
    cp $EXPDIR/$EXPNAME/cmvn_opts                             $DISTDIR/$AMNAME/model/ 2>/dev/null 
    cp $EXPDIR/$EXPNAME/tree                                  $DISTDIR/$AMNAME/model/ 2>/dev/null 

    cp $EXPDIR/$EXPNAME/graph/HCLG.fst                        $DISTDIR/$AMNAME/model/
    cp $EXPDIR/$EXPNAME/graph/words.txt                       $DISTDIR/$AMNAME/model/
    cp $EXPDIR/$EXPNAME/graph/num_pdfs                        $DISTDIR/$AMNAME/model/
    cp $EXPDIR/$EXPNAME/graph/phones/*                        $DISTDIR/$AMNAME/model/
    cp $EXPDIR/$EXPNAME/graph/phones.txt                      $DISTDIR/$AMNAME/model/

    cp data/dst/asr-models/kaldi/${MODEL}/data/local/dict/*   $DISTDIR/$AMNAME/model/

    if [ -e $EXPDIR/extractor/final.mat ] ; then

        mkdir -p "$DISTDIR/$AMNAME/extractor"

        cp $EXPDIR/extractor/final.mat                  "$DISTDIR/$AMNAME/extractor/"
        cp $EXPDIR/extractor/global_cmvn.stats          "$DISTDIR/$AMNAME/extractor/"
        cp $EXPDIR/extractor/final.dubm                 "$DISTDIR/$AMNAME/extractor/"
        cp $EXPDIR/extractor/final.ie                   "$DISTDIR/$AMNAME/extractor/"
        cp $EXPDIR/extractor/splice_opts                "$DISTDIR/$AMNAME/extractor/"
        cp $EXPDIR/ivectors_test_hires/conf/splice.conf "$DISTDIR/$AMNAME/extractor/"

    fi

    cp data/dst/asr-models/kaldi/${MODEL}/RESULTS.txt $DISTDIR/$AMNAME/
    cp README.md "$DISTDIR/$AMNAME"
    cp LICENSE   "$DISTDIR/$AMNAME"
    cp AUTHORS   "$DISTDIR/$AMNAME"

    mkdir -p "$DISTDIR/$AMNAME/conf"
    cp data/src/speech/kaldi-mfcc.conf        $DISTDIR/$AMNAME/conf/mfcc.conf 
    cp data/src/speech/kaldi-mfcc-hires.conf  $DISTDIR/$AMNAME/conf/mfcc-hires.conf  
    cp data/src/speech/kaldi-online-cmvn.conf $DISTDIR/$AMNAME/conf/online_cmvn.conf

    pushd $DISTDIR
    tar cfv "$AMNAME.tar" $AMNAME
    xz -v -8 -T 12 "$AMNAME.tar"
    popd

    rm -r "$DISTDIR/$AMNAME"

fi

if [ $WHAT = "sphinx_cont" ] ; then

    #
    # cont sphinx model
    #

    DISTDIR=data/dist/asr-models

    AMNAME="cmusphinx-cont-${MODEL}-r$datum"
    echo "$AMNAME ..."

    mkdir -p "$DISTDIR/$AMNAME"
    mkdir -p "$DISTDIR/$AMNAME/model_parameters"

    cp -r data/dst/asr-models/cmusphinx_cont/${MODEL}/model_parameters/voxforge.cd_cont_6000 "$DISTDIR/$AMNAME/model_parameters"
    cp -r data/dst/asr-models/cmusphinx_cont/${MODEL}/etc "$DISTDIR/$AMNAME"
    cp    data/dst/asr-models/cmusphinx_cont/${MODEL}/voxforge.html "$DISTDIR/$AMNAME"
    cp README.md "$DISTDIR/$AMNAME"
    cp LICENSE   "$DISTDIR/$AMNAME"
    cp AUTHORS   "$DISTDIR/$AMNAME"

    pushd $DISTDIR
    tar cfv "$AMNAME.tar" $AMNAME
    xz -v -8 -T 12 "$AMNAME.tar"
    popd

    rm -r "$DISTDIR/$AMNAME"
fi

if [ $WHAT = "sphinx_ptm" ] ; then

    #
    # ptm sphinx model
    #

    DISTDIR=data/dist/asr-models

    AMNAME="cmusphinx-ptm-${MODEL}-r$datum"
    echo "$AMNAME ..."

    mkdir -p "$DISTDIR/$AMNAME"
    mkdir -p "$DISTDIR/$AMNAME/model_parameters"

    cp -r data/dst/asr-models/cmusphinx_ptm/${MODEL}/model_parameters/voxforge.cd_ptm_5000 "$DISTDIR/$AMNAME/model_parameters"
    cp -r data/dst/asr-models/cmusphinx_ptm/${MODEL}/etc "$DISTDIR/$AMNAME"
    cp    data/dst/asr-models/cmusphinx_ptm/${MODEL}/voxforge.html "$DISTDIR/$AMNAME"
    cp README.md "$DISTDIR/$AMNAME"
    cp LICENSE   "$DISTDIR/$AMNAME"
    cp AUTHORS   "$DISTDIR/$AMNAME"

    pushd $DISTDIR
    tar cfv "$AMNAME.tar" $AMNAME
    xz -v -8 -T 12 "$AMNAME.tar"
    popd

    rm -r "$DISTDIR/$AMNAME"
fi

if [ $WHAT = "srilm" ] ; then
    #
    # srilm
    #

    DISTDIR=data/dist/lm

    LMNAME="srilm-${MODEL}-r$datum.arpa"
    echo "$LMNAME ..."
    # data/dst/lm/generic_de_lang_model/
    cp data/dst/lm/${MODEL}/lm.arpa ${DISTDIR}/$LMNAME
    gzip ${DISTDIR}/$LMNAME
fi

if [ $WHAT = "sequitur" ] ; then
    #
    # sequitur
    #

    DISTDIR=data/dist/g2p

    MODELNAME="sequitur-${MODEL}-r$datum"
    echo "$MODELNAME ..."
    cp data/dst/dict-models/${MODEL}/sequitur/model-6 $DISTDIR/$MODELNAME
    gzip $DISTDIR/$MODELNAME
fi

#
# copyright info
#

cp README.md "$DISTDIR"
cp LICENSE   "$DISTDIR"
cp AUTHORS   "$DISTDIR"

#
# upload
#

echo rsync -avPz --delete --bwlimit=256 data/dist/ goofy:/var/www/html/voxforge/

