#!/usr/bin/env bash
set -eu

SERVERS="pulsar batch"
BENCHMARKS="chipseq-pe.yml rnaseq.yml variant.yml variant-test.yml"

for server in $SERVERS ; do
    for benchmark in $BENCHMARKS ; do
        echo "Validating $benchmark on the $server server"
        abm $server benchmark validate benchmarks/$benchmark
    done
done

