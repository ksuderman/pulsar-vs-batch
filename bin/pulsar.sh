#!/usr/bin/env bash
set -eu

BRANCH=gcs-and-pulsar
SERVER=ks-pulsar-test
REPO=${REPO:-https://github.com/ksuderman/galaxy-k8s-boot}
export ZONE=us-east4-c

# ANSI formatting
reset="\033[0m"
bold="\033[1m"

function hi() {
    echo -e "$bold$@$reset"
}

NAME=$(basename "$0")

function help() {
    cat << EOF

$(hi NAME)
    $NAME

$(hi DESCRIPTION)
    Quick-start wrapper around $(hi launch_vm.sh) with preset defaults for
    launching a Galaxy Kubernetes VM with the Pulsar GCP Batch job runner enabled.

$(hi SYNOPSIS)
    $NAME [start|stop|help]

$(hi OPTIONS)
    $(hi start)             start a Galaxy VM that uses the pulsar batch runner
    $(hi stop)              stop the Galaxy VM
    $(hi bounce)            stops the Galaxy VM and then starts it again
    $(hi -h)|$(hi --help)|$(hi help)    show this help message

$(hi EXAMPLES)
    \$> $NAME
    \$> $NAME start
    \$> $NAME stop
    \$> $NAME help

EOF
}

if [[ $# -eq 0 ]] ; then
	help
	exit
fi

function start() {
	echo "Launching ${SERVER}"
	bin/launch_vm.sh $SERVER \
	  --git-repo $REPO \
	  --git-branch $BRANCH \
	  --disk-size 1024 \
	  --enable-pulsar-gcp \
	  -f values/values.yml \
	  -f mixins/local.yml \
	  -f mixins/pulsar-batch.yml 
#	echo "Waiting for the server to come up."
#	sleep 10
#	bin/tail.sh $SERVER
}

function stop() {
	echo "Stopping $SERVER"
	gcloud compute instances delete $SERVER --zone $ZONE --quiet
	for disk in $(gcloud compute disks list --filter="name~.*${SERVER}.*" --format='value(name)') ; do
		gcloud compute disks delete $disk --zone $ZONE --quiet
	done
}

case $1 in
	kube)
		if [[ -e .kubeconfig ]] ; then
			rm .kubeconfig
		fi
		bin/kube.sh --server $SERVER --cloud pulsar
		;;
	start) start ;;
	stop) stop ;;
	bounce)
		stop
		start		
		;;
	-h|--help|help)
		help
		exit
		;;
	*)
		echo "Unrecognized parameter $1"
		help
		exit 1
		;;
esac
