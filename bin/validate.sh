#!/usr/bin/env bash
set -eu

SERVERS=${1:-"pulsar batch single"}
BENCHMARKS="chipseq-pe.yml rnaseq.yml variant.yml"

for server in $SERVERS ; do
    for benchmark in $BENCHMARKS ; do
        echo "Validating $benchmark on the $server server"
        abm $server benchmark validate benchmarks/$benchmark
    done
done

