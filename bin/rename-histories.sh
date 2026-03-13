#!/usr/bin/env bash
set -eu

if [[ $# -eq 0 ]] ; then
    echo "USAGE: $0 [batch,pulsar]"
    exit 1
fi

while [[ $# -gt 0 ]] ; do
    case $1 in
        batch|pulsar)
            cloud=$1
            abm $cloud history list | grep imported | while read -r input ; do
                hid=$(echo $input | awk '{print $1}')
                new_name=$(echo $input | sed 's/.*imported from archive: //g' | sed 's/ False.*False//')
                echo "Renaming history $hid to '$new_name'"
                abm $cloud history rename $hid "$new_name"
            done
            ;;
        *)
            echo "Invalid option."
            exit
            ;;
    esac
    shift
done