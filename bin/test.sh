#!/usr/bin/env bash
set -eu

if [[ $# -eq 0 ]] ; then
    echo "USAGE: $0 [batch|pulsar]"
    exit 1
fi
CMD=validate
while [[ $# -gt 0 ]] ; do
    case $1 in
        batch|pulsar)
            abm $1 bench $CMD $(pwd)/benchmarks/variant-test.yml
            ;;
        run) CMD=run ;;
        validate) CMD=validate ;;
        *)
            echo "Unknown option $1"
            echo "Must be one of batch or pulsar"
            exit 1
            ;;
    esac
    shift
done
#echo "To run the benchmark run the command:"
#echo "    abm $cloud bench validate $(pwd)/benchmarks/variant-test.yml"
#echo ""
