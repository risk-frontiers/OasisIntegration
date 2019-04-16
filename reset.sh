#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export UI_VER='1.0.2'

read -r -p "Are you sure to delete all data (setting, portfolio, calculated losses, ...) for this deployment?
Note that this is very dangerous especially if you have another instance of oasislmf on this same infrastructure [y/N] " response
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

    echo "Deleting networks"
    docker network rm oasis_default
    docker network rm shiny-net

    echo "Deleting persistent data"
    cd ${SCRIPT_DIR}
    if [[ -d db-data ]]
        then sudo rm -r db-data
    fi
    if [[ -d docker-shared-fs ]]
        then sudo rm -r docker-shared-fs
    fi
fi