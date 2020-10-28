#!/usr/bin/env bash

re='^[0-9]+$'

if [[ $# -eq 0 ]] || [[ ! $1 =~ $re ]]
then
        echo 'Error: this command needs an integer argument. The number of processes should not be too large but it depends on your hardware. A rule of thumb is to use 1 if memory is lower than 96 GB and 2 to 4 otherwise.'
        echo 'For instance, run'
        echo '  ./set_ktools_num_processes 2'
        exit 1
fi
sed -i '/ktools_num_processes/c\    "ktools_num_processes": '$1',' /home/worker/complex_model/oasislmf.json