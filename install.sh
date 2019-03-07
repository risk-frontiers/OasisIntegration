#!/bin/bash
export OASIS_VER='1.0.0'


# SETUP AND RUN COMPLEX MODEL EXAMPLE
    COMPOSE_PLATFORM='docker-compose.yml'
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    sed -i 's|:latest|:${OASIS_VER}|g' $SCRIPT_DIR/$COMPOSE_PLATFORM

    docker build -f Dockerfile.custom_model_worker -t coreoasis/custom_model_worker:$OASIS_VER .
    docker-compose up -d


# RUN OASIS UI
    GIT_UI=OasisUI
    if [ -d $SCRIPT_DIR/$GIT_UI ]; then
        cd $SCRIPT_DIR/$GIT_UI
        git pull
    else
        git clone https://github.com/OasisLMF/$GIT_UI.git -b $BRANCH_UI
    fi 

    docker network create shiny-net
    docker pull coreoasis/oasisui_app
    docker-compose -f $SCRIPT_DIR/$GIT_UI/docker-compose.yml up -d
