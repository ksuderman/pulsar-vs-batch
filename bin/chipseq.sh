#!/usr/bin/env bash

for size in 2g 5g 10g ; do
	history=chipseq-$size
	for server in pulsar single ; do
		echo "Importing $history to $server"
		abm $server history import $history &
	done
	wait
done
