#!/bin/bash

if [ $# -lt 2 ] ; then
    echo "usage: $0 [-c] <model> [kaldi <experiment>|sphinx_cont|sphinx_ptm|sequitur|lm|voice <epoch>|w2l <experiment>]"
    exit 1
fi

# parse command line options

datum=`date +%Y%m%d`

REVISION="r$datum"

while [ -n "$1" ] ;do
 
    case "$1" in
        -c) REVISION='current';;

        *) break;; 
 
    esac

    shift
 
done

MODEL=$1
WHAT=$2

if [ $WHAT = "kaldi" ] ; then

    if [ $# != 3 ] ; then
        echo "usage: $0 [-c] <model> [kaldi <experiment>|sphinx_cont|sphinx_ptm|sequitur|lm|voice <epoch>|w2l <experiment>]"
        exit 2
    fi

    DISTDIR=data/dist/asr-models
    EXPNAME=$3

    if [ -e data/dst/asr-models/kaldi/${MODEL}/exp/nnet3_chain/${EXPNAME} ] ; then
        EXPDIR="data/dst/asr-models/kaldi/${MODEL}/exp/nnet3_chain"
    else
        EXPDIR="data/dst/asr-models/kaldi/${MODEL}/exp"
    fi

    AMNAME="kaldi-${MODEL}-${EXPNAME}-${REVISION}"


    echo "$AMNAME ..."

    rm -rf "$DISTDIR/$AMNAME"
    mkdir -p "$DISTDIR/$AMNAME/model"

    cp $EXPDIR/$EXPNAME/final.mdl                               $DISTDIR/$AMNAME/model/
    cp $EXPDIR/$EXPNAME/final.mat                               $DISTDIR/$AMNAME/model/ 2>/dev/null
    cp $EXPDIR/$EXPNAME/final.occs                              $DISTDIR/$AMNAME/model/ 2>/dev/null
    cp $EXPDIR/$EXPNAME/full.mat                                $DISTDIR/$AMNAME/model/ 2>/dev/null
    cp $EXPDIR/$EXPNAME/splice_opts                             $DISTDIR/$AMNAME/model/ 2>/dev/null
    cp $EXPDIR/$EXPNAME/cmvn_opts                               $DISTDIR/$AMNAME/model/ 2>/dev/null 
    cp $EXPDIR/$EXPNAME/tree                                    $DISTDIR/$AMNAME/model/ 2>/dev/null 

    mkdir -p "$DISTDIR/$AMNAME/model/graph"

    cp $EXPDIR/$EXPNAME/graph/HCLG.fst                          $DISTDIR/$AMNAME/model/graph/
    cp $EXPDIR/$EXPNAME/graph/words.txt                         $DISTDIR/$AMNAME/model/graph/
    cp $EXPDIR/$EXPNAME/graph/num_pdfs                          $DISTDIR/$AMNAME/model/graph/
    cp $EXPDIR/$EXPNAME/graph/phones.txt                        $DISTDIR/$AMNAME/model/graph/

    mkdir -p "$DISTDIR/$AMNAME/model/graph/phones"
    cp $EXPDIR/$EXPNAME/graph/phones/*                          $DISTDIR/$AMNAME/model/graph/phones/

    if [ -e $EXPDIR/extractor/final.mat ] ; then

        mkdir -p "$DISTDIR/$AMNAME/extractor"

        cp $EXPDIR/extractor/final.mat                          $DISTDIR/$AMNAME/extractor/
        cp $EXPDIR/extractor/global_cmvn.stats                  $DISTDIR/$AMNAME/extractor/
        cp $EXPDIR/extractor/final.dubm                         $DISTDIR/$AMNAME/extractor/
        cp $EXPDIR/extractor/final.ie                           $DISTDIR/$AMNAME/extractor/
        cp $EXPDIR/extractor/splice_opts                        $DISTDIR/$AMNAME/extractor/

        mkdir -p "$DISTDIR/$AMNAME/ivectors_test_hires/conf"

        cp $EXPDIR/ivectors_test_hires/conf/ivector_extractor.conf  $DISTDIR/$AMNAME/ivectors_test_hires/conf/
        cp $EXPDIR/ivectors_test_hires/conf/online_cmvn.conf        $DISTDIR/$AMNAME/ivectors_test_hires/conf/
        cp $EXPDIR/ivectors_test_hires/conf/splice.conf             $DISTDIR/$AMNAME/ivectors_test_hires/conf/

    fi

    mkdir -p "$DISTDIR/$AMNAME/data/local/dict"
    cp data/dst/asr-models/kaldi/${MODEL}/data/local/dict/*     $DISTDIR/$AMNAME/data/local/dict/

    cp -rp data/dst/asr-models/kaldi/${MODEL}/data/lang         $DISTDIR/$AMNAME/data/

    mkdir -p "$DISTDIR/$AMNAME/conf"
    cp data/dst/asr-models/kaldi/${MODEL}/conf/mfcc.conf        $DISTDIR/$AMNAME/conf/mfcc.conf 
    cp data/dst/asr-models/kaldi/${MODEL}/conf/mfcc_hires.conf  $DISTDIR/$AMNAME/conf/mfcc_hires.conf  
    cp data/dst/asr-models/kaldi/${MODEL}/conf/online_cmvn.conf $DISTDIR/$AMNAME/conf/online_cmvn.conf

    cp data/dst/asr-models/kaldi/${MODEL}/RESULTS.txt $DISTDIR/$AMNAME/
    cp README.md "$DISTDIR/$AMNAME"
    cp LICENSE   "$DISTDIR/$AMNAME"
    cp AUTHORS   "$DISTDIR/$AMNAME"

    pushd $DISTDIR
    rm -f "$AMNAME.tar" "$AMNAME.tar.xz"
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

    AMNAME="cmusphinx-cont-${MODEL}-${REVISION}"
    echo "$AMNAME ..."

    mkdir -p "$DISTDIR/$AMNAME"
    mkdir -p "$DISTDIR/$AMNAME/model_parameters"

    cp -r data/dst/asr-models/cmusphinx_cont/${MODEL}/model_parameters/voxforge.cd_cont_* "$DISTDIR/$AMNAME/model_parameters"
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

    AMNAME="cmusphinx-ptm-${MODEL}-${REVISION}"
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

if [ $WHAT = "lm" ] ; then
    #
    # KenLM
    #

    DISTDIR=data/dist/lm

    LMNAME="${MODEL}-${REVISION}.arpa"
    echo "$LMNAME ..."
    cp data/dst/lm/${MODEL}/lm.arpa ${DISTDIR}/$LMNAME
    xz -9 -v ${DISTDIR}/$LMNAME
fi

if [ $WHAT = "sequitur" ] ; then
    #
    # sequitur
    #

    DISTDIR=data/dist/g2p

    MODELNAME="sequitur-${MODEL}-${REVISION}"
    echo "$MODELNAME ..."
    cp data/dst/dict-models/${MODEL}/sequitur/model-6 $DISTDIR/$MODELNAME
    gzip $DISTDIR/$MODELNAME
fi

if [ $WHAT = "voice" ] ; then

    if [ $# != 3 ] ; then
        echo "usage: $0 [-c] <model> [kaldi <experiment>|sphinx_cont|sphinx_ptm|sequitur|lm|voice <epoch>]"
        exit 2
    fi

    DISTDIR=data/dist/tts
    EPOCH=$3
    ARCNAME="voice-${MODEL}-${EPOCH}-${REVISION}"

    echo "${ARCNAME}..."

    echo rm -rf "$DISTDIR/$ARCNAME*"
    rm -rf "$DISTDIR/$ARCNAME*"
    mkdir -p "$DISTDIR/$ARCNAME"

    cp data/dst/tts/voices/${MODEL}/cp/cp${EPOCH}-*.data-00000-of-00001 "$DISTDIR/$ARCNAME/model.data-00000-of-00001"
    cp data/dst/tts/voices/${MODEL}/cp/cp${EPOCH}-*.index               "$DISTDIR/$ARCNAME/model.index"
    cp data/dst/tts/voices/${MODEL}/cp/cp${EPOCH}-*.meta                "$DISTDIR/$ARCNAME/model.meta"
    cp data/dst/tts/voices/${MODEL}/hparams.json                        "$DISTDIR/$ARCNAME/hparams.json"

    cp README.md LICENSE AUTHORS                                        "$DISTDIR/$ARCNAME/"

    pushd $DISTDIR
    tar cfv "$ARCNAME.tar" $ARCNAME
    xz -v -8 -T 12 "$ARCNAME.tar"
    popd

    rm -r "$DISTDIR/$ARCNAME"

fi

if [ $WHAT = "w2l" ] ; then

    if [ $# != 3 ] ; then
        echo "usage: $0 [-c] <model> [kaldi <experiment>|sphinx_cont|sphinx_ptm|sequitur|lm|voice <epoch>|w2l <experiment>]"
        exit 2
    fi

    DISTDIR=data/dist/asr-models
    EXPNAME=$3

    AMNAME="w2l-${MODEL}-${REVISION}"

    SRCDIR="data/dst/asr-models/wav2letter/${MODEL}"

    echo "$AMNAME ..."

    rm -rf "$DISTDIR/$AMNAME"
    mkdir -p "$DISTDIR/$AMNAME"

    lastone=`ls -t ${SRCDIR}/models/${EXPNAME}/*last.bin | head -n 1`
    echo $lastone

    cp ${lastone}                                      $DISTDIR/$AMNAME/model.bin
    cp ${SRCDIR}/data/tokens.txt                       $DISTDIR/$AMNAME/
    cp ${SRCDIR}/data/lexicon.txt                      $DISTDIR/$AMNAME/

    cp README.md "$DISTDIR/$AMNAME"
    cp LICENSE   "$DISTDIR/$AMNAME"
    cp AUTHORS   "$DISTDIR/$AMNAME"

    pushd $DISTDIR
    rm -f "$AMNAME.tar" "$AMNAME.tar.xz"
    tar cfv "$AMNAME.tar" $AMNAME
    xz -v -8 -T 12 "$AMNAME.tar"
    popd

    rm -r "$DISTDIR/$AMNAME"

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

echo rsync -avPz --delete --bwlimit=256 data/dist/ goofy:/var/www/html/zamia-speech/

