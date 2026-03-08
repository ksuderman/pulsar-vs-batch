#!/usr/bin/env bash

SERVER=${SERVER:-batch}

if [[ $# -gt 0 ]] ; then
	SERVER=$1
fi

gcloud compute ssh ks-$SERVER-test --project=anvil-and-terra-development --zone=us-east4-c --command='sudo tail -f /var/log/cloud-init-output.log'