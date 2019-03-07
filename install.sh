#!/bin/bash
export OASIS_VER='1.0.0'
export UI_VER='1.0.0'
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# SETUP AND RUN COMPLEX MODEL EXAMPLE
    # Reset compose file to last commit && update tag number 
    git checkout -- docker-compose.yml
    sed -i 's|:latest|:${OASIS_VER}|g' $SCRIPT_DIR/$COMPOSE_PLATFORM

    # reset and build custom worker
    ggit checkout -- Dockerfile.custom_model_worker
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
    cd $SCRIPT_DIR/$GIT_UI
    git checkout -- docker-compose.yml
    sed -i 's|:latest|:${UI_VER}|g' $GIT_UI/docker-compose.yml
    cd $SCRIPT_DIR

    # Start UI
    docker network create shiny-net
    docker pull coreoasis/oasisui_app:$UI_VER
    docker-compose -f $SCRIPT_DIR/$GIT_UI/docker-compose.yml up -d
