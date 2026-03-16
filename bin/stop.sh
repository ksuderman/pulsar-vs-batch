#!/usr/bin/env bash
set -e

if [[ $# -eq 0 ]] ; then
	echo "No cloud/instance names provided."
	echo "USAGE: $0 pulsar batch bucket"
	exit 1
fi

for server in $@ ; do
	bin/$server.sh stop &
done
wait
echo "All instances stopped."