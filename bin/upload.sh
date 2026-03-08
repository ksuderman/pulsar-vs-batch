#!/usr/bin/env bash
set -eu

for cloud in $@ ; do
    echo "Uploading data and workflows to $cloud"
    hid=$(abm $cloud history create "ChipSeq-PE Input Data" | jq -r .id)
    abm $cloud dataset import --name forward --history $hid chipseq-1
    abm $cloud dataset import --name reverse --history $hid chipseq-2
    for history in rna rna-20 rna-50 variant-test variant-2g variant-5g variant-10g ; do
        echo "Importing history $history to $cloud"
        abm $cloud history import $history
    done
    for workflow in rnaseq-pe variant chipseq-pe ; do
        echo "Importing workflow $workflow to $cloud"
        abm $cloud workflow import $workflow
    done
    # Trying to create the dataset collection before the datasets have finished
    # uploading will fail.  Doing it at the very end should avoid that.
    abm $cloud dataset collection wt_H3K4me3=forward,reverse
done