#!/usr/bin/env bash
set -eu

if [[ $# -eq 0 ]] ; then
    echo "USAGE: $0 [batch|bucket|pulsar]"
    exit 1
fi
function get_dataset_id() {
    echo "Getting dataset collection ID is history $2"
    echo $(abm $1 dataset list --history "$2" | grep dataset_collection | awk '{print $1'})
}

function rename_rnaseq_dataset() {
    cloud=$1
    history=$2
    suffix=$3
    dsid=$(get_dataset_id $cloud "$history")
    echo abm $cloud dataset rename "$history" $dsid "SRR24043307-$suffix"
    abm $cloud dataset rename "$history" $dsid "SRR24043307-$suffix"
}

while [[ $# -gt 0 ]] ; do
    case $1 in
        batch|bucket|pulsar)
            for size in 2GB 5GB 10GB ; do
                dsid=$(get_dataset_id $1 "Variant calling inputs - $size")
                echo abm $1 dataset rename "Variant calling inputs - $size" $dsid SRR24043307-$size
                abm $1 dataset rename "Variant calling inputs - $size" $dsid SRR24043307-$size
            done
            rename_rnaseq_dataset $1 SRR24043307-downsampled-80 "80"
            rename_rnaseq_dataset $1 SRR24043307-downsampled-50 "50"
            rename_rnaseq_dataset $1 SRR24043307-full "full"
            ;;
        *)
            echo "Invalid parameter: $1"
            ;;
    esac
    shift
done
