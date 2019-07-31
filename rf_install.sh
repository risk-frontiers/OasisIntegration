#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODEL_DATA=${SCRIPT_DIR}/"model_data"

export OASIS_VER='1.2.0'
export UI_VER='1.2.0'

cd ${SCRIPT_DIR}

# verify model data
if [[ -d ${MODEL_DATA} ]]
    then cd ${MODEL_DATA}
    if [[ ! -f "license.txt" ]]
        then echo "License file missing. Please copy your Risk Frontiers license file in the model_data folder."
        exit 1
    fi

    if [[ ! -f "events.bin" ]]
        then echo "This is not a valid model data directory: events.bin missing"
        exit 1
    fi

    if [[ ! -f "events_p.bin" ]]
        then echo "Creating events_p.bin"
        cp events.bin events_p.bin
    fi
    if [[ ! -f "events_h.bin" ]]
        then echo "Creating events_h.bin"
        cp events.bin events_h.bin
    fi

    if [[ ! -f "occurrence.bin" ]]
        then echo "This is not a valid model data directory: occurrence.bin missing"
        exit 1
    fi

    if [[ ! -f "occurrence_1.bin" ]]
        then echo "Creating occurrence_1.bin"
        cp occurrence.bin occurrence_1.bin
    fi
else
    echo "WARNING: Directory model_data missing. This installation will not work properly without the data folder."
fi

# SETUP and RUN complex
echo "Setting up docker images and containers for Oasis worker and API"
cd ${SCRIPT_DIR}
#git checkout -- docker-compose.yml
sed -i 's|:latest|:${OASIS_VER}|g' docker-compose.yml

# reset and build custom worker
#git checkout -- Dockerfile.custom_model_worker
sed -i "s|:latest|:${OASIS_VER}|g" Dockerfile.custom_model_worker
docker pull coreoasis/model_worker:${OASIS_VER}
docker build -f Dockerfile.custom_model_worker -t coreoasis/custom_model_worker:${OASIS_VER} .

# Start API
docker-compose up -d

# RUN OASIS UI
GIT_UI=OasisUI
if [[ -d ${SCRIPT_DIR}/${GIT_UI} ]]; then
    cd ${SCRIPT_DIR}/${GIT_UI}
    git fetch
    git checkout ${UI_VER}
else
    git clone https://github.com/OasisLMF/${GIT_UI}.git -b ${UI_VER}
fi 

# Reset UI docker Tag
cd ${SCRIPT_DIR}/${GIT_UI}
git checkout -- docker-compose.yml
sed -i 's|:latest|:${UI_VER}|g' docker-compose.yml
cd ${SCRIPT_DIR}

# Start UI
echo "Setting up docker images and containers for Oasis UI"
cp ${SCRIPT_DIR}/model_resource.json ${SCRIPT_DIR}/${GIT_UI}/model_resource.json
docker network create shiny-net
docker pull coreoasis/oasisui_app:${UI_VER}
docker-compose -f ${SCRIPT_DIR}/${GIT_UI}/docker-compose.yml up -d
