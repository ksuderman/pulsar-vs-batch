#!/usr/bin/env bash

SERVER=$1
JOB_ID=$2

JSON_DATA=$(abm $SERVER job show $JOB_ID)

start=$(echo $JSON_DATA | jq -r .create_time)
end=$(echo $JSON_DATA | jq -r .update_time)
elapsed=$(( $(date -d "$end" +%s) - $(date -d "$start" +%s) ))
date -u -d "@$elapsed" +%H:%M:%S
