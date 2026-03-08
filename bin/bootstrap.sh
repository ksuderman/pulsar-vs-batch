#!/usr/bin/env bash

set -eu

MASTER_API_KEY=galaxypassword
GALAXY_USER=default-user

for cloud in $@ ; do
    server="ks-$cloud-test"
    echo "Bootstrapping $server"
    url=http://$(gcloud compute instances list --filter="name~${server}" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
    abm config url $cloud $url
    abm config key $cloud $MASTER_API_KEY
    # Make sure the default user has been created
    curl -s $url > /dev/null
    key=$(abm $cloud user key $GALAXY_USER)
    abm config key $cloud $key
done
