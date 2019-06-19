#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export UI_VER='1.1.3'

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

    echo "Removing UI containers (UI version: ${UI_VER})"
    docker rm -f $(docker ps -a -q --filter ancestor="coreoasis/oasisui_app:${UI_VER}")
    docker rm -f $(docker ps -a -q --filter ancestor="coreoasis/oasisui_proxy:${UI_VER}")

    #echo "Deleting networks"
    #docker network rm oasis_default
    #docker network rm shiny-net

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