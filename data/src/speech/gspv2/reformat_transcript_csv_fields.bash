#!/bin/bash

# Reformat the first and second columns in transcripts_00.csv
#
# This script was used to reformat the first two columns in transcripts_00.csv.
# Its purpose in the repo is only to document how the columns have been modifed.
# After the new format has been deemed ok, this file can be removed from the
# repo.
#
# Example transformation for column 0:
#
# from gsp01deac0b92bd44ed8a89ceceaf5da3fc_2015-02-09-15-08-07-Kinect-Beam
#   to gsp01deac0b92bd44ed8a89ceceaf5da3fc-1_2015-02-09-15-08-07-Kinect-Beam
#
# Example transformation for column 1:
#
# from gsp01deac0b92bd44ed8a89ceceaf5da3fc
#   to gsp01deac0b92bd44ed8a89ceceaf5da3fc-1

SRC_TRANSCRIPTS_CSV=transcripts_00.csv
DST_TRANSCRIPTS_CSV=new_transcripts_00.csv

sed -e 's/_2014-/-1_2014-/g' \
    -e 's/_2015-/-1_2015-/g' \
    ${SRC_TRANSCRIPTS_CSV} \
    | awk 'BEGIN{FS=";"; OFS=";"} {$2 = $2 "-1"; print($0)}' \
    > ${DST_TRANSCRIPTS_CSV}
