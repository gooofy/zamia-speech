#!/bin/bash

#
# mfcc
#

echo "computing MFCC..."

bash run-feat.sh

#
# language model
#

#cat prompts.sent > all.sent
cat prompts.sent ../sentences.txt > all.sent

sed 's/^/<s> /' all.sent | sed 's/$/ <\/s>/' >all.txt

echo '</s>' > all.vocab
echo '<s>' >> all.vocab
cat wlist.txt >>all.vocab

text2idngram -vocab all.vocab -idngram voxforge.idngram < all.txt
idngram2lm -calc_mem -vocab_type 0 -idngram voxforge.idngram -vocab all.vocab -arpa voxforge.arpa
sphinx_lm_convert -i voxforge.arpa -o etc/voxforge.lm.DMP

#
# sphintrain
#

# sphinxtrain -s verify,g2p_train,lda_train,mllt_train,vector_quantize,falign_ci_hmm,force_align,vtln_align,ci_hmm,cd_hmm_untied,buildtrees,prunetree,cd_hmm_tied,lattice_generation,lattice_pruning,lattice_conversion,mmie_train,deleted_interpolation,decode run 2>&1 | tee logs/sphinxtrain_run.log
time sphinxtrain run 2>&1 | tee logs/sphinxtrain_run.log

