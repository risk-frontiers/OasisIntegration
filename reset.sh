#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

file_docker='docker/Dockerfile'
file_versions='data_version.json'

# Read and set versions
env_vars=('OASIS_API_VER' 'OASIS_UI_VER' 'MODEL_VER' 'DATA_VER' 'INTEGRATION_VER' 'KTOOLS_VER' 'OASISLMF_VER')
for var_name in "${env_vars[@]}"; do
        var_value=$(cat ${file_versions} | grep ${var_name} | awk -F'"' '{ print $4 }')
    export ${var_name}=${var_value}
done

read -r -p "Are you sure you want to reset this deployment?
Note that running this script on a shared deployment (i.e. an Oasis deployment including multiple
models from the same or different vendors) is **VERY DANGEROUS**. Please use this for technical testing of
Risk Frontiers integration only. Once the Oasis UI is stable enough, this script will be removed. [y/N] " response
response=${response,,}    # to lower
if [[ "$response" =~ ^(yes|y)$ ]]
then
    echo "Removing API and worker containers"
    docker rm -f oasis_api_server
    docker rm -f oasis_worker_monitor
    docker rm -f oasis_complex_model
    docker rm -f oasis_server_db
    docker rm -f oasis_celery_db
    docker rm -f oasis_rabbit
    docker rm -f oasis_flower
    docker rm -f oasis_user-interface_1
    docker rm -f oasisintegration_user-interface_1
    docker rm -f oasisui_proxy

    echo "Removing custom worker image"
    docker rmi coreoasis/rf_hail:${INTEGRATION_VER}

    echo "Pruning obsolete images and networks"
    docker system prune

    read -r -p "Do you want to to delete all data (setting, portfolio, calculated losses, logs, tmp ...)? [y/N]" response
    response=${response,,}    # to lower
    if [[ "$response" =~ ^(yes|y)$ ]]
     then
        cd ${SCRIPT_DIR}
        if [[ -d db-data ]]
            then sudo rm -r db-data
        fi
        if [[ -d docker-shared-fs ]]
            then sudo rm -r docker-shared-fs
        fi
        if [[ -d log ]]
            then sudo rm -r log
        fi
        if [[ -d tmp ]]
            then sudo rm -r tmp
        fi
    fi
fi