#!/bin/bash
export OASIS_VER='1.0.0'
export UI_VER='1.0.0-rc1'

# SETUP AND RUN COMPLEX MODEL EXAMPLE
    COMPOSE_PLATFORM='docker-compose.yml'
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

    # Reset compose file to last commit && update tag number 
    git checkout HEAD^ $COMPOSE_PLATFORM
    sed -i 's|:latest|:${OASIS_VER}|g' $SCRIPT_DIR/$COMPOSE_PLATFORM

    # reset and build custom worker
    git checkout HEAD^ Dockerfile.custom_model_worker
    sed -i "s|:latest|:${OASIS_VER}|g" $SCRIPT_DIR/Dockerfile.custom_model_worker
    docker build -f Dockerfile.custom_model_worker -t coreoasis/custom_model_worker:$OASIS_VER .

    # Start API
    docker-compose up -d


# RUN OASIS UI
    GIT_UI=OasisUI
    if [ -d $SCRIPT_DIR/$GIT_UI ]; then
        cd $SCRIPT_DIR/$GIT_UI
        git checkout $UI_VER
    else
        git clone https://github.com/OasisLMF/$GIT_UI.git -b $UI_VER
    fi 

    # Reset UI docker Tag
    git checkout HEAD^ $GIT_UI/docker-compose.yml
    sed -i 's|:latest|:${UI_VER}|g' $GIT_UI/docker-compose.yml

    # Start UI
    docker network create shiny-net
    docker pull coreoasis/oasisui_app:$UI_VER
    docker-compose -f $SCRIPT_DIR/$GIT_UI/docker-compose.yml up -d
