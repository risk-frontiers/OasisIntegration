#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODEL_DATA=${SCRIPT_DIR}/"model_data"

export OASIS_VER='1.2.0'
export OASIS_UI_VER='1.2.0'

file_docker='docker/Dockerfile'
file_versions='data_version.json'
# Read and set versions
    env_vars=('OASIS_API_VER' 'OASIS_UI_VER' 'MODEL_VER' 'DATA_VER')
    for var_name in "${env_vars[@]}"; do
            var_value=$(cat $file_versions | grep $var_name | awk -F'"' '{ print $4 }')
        export $var_name=$var_value
    done

cd ${SCRIPT_DIR}
# Customize BATCH_COUNT in conf.ini
# Ideally between 10 and 16 which represents the memory consumption by each independent RF .net engine
# OASIS financial engine is quite memory intensive so we simply reserve twice as much memory at the moment
SCALE_FACTOR=16 # = 20 * 2
BATCH_COUNT=$(expr `awk '/MemFree/ { printf "%.0f \n", $2/1024/1024 }' /proc/meminfo` / ${SCALE_FACTOR})
BATCH_COUNT=$([ ${BATCH_COUNT} -le 1 ] && echo 1 || echo ${BATCH_COUNT})
VCPU_COUNT=$(cat /proc/cpuinfo | awk '/^processor/{print $3}' | wc -l)
BATCH_COUNT=$([ ${VCPU_COUNT} -le ${BATCH_COUNT} ] && echo ${VCPU_COUNT} || echo ${BATCH_COUNT})
sed -i '/KTOOLS_BATCH_COUNT/c\KTOOLS_BATCH_COUNT = '${BATCH_COUNT} conf.ini

# verify model data
if [[ -d ${MODEL_DATA} ]]
    then cd ${MODEL_DATA}
    if [[ ! -f "license.txt" ]] && [[ ! -f "licence.txt" ]]
        then echo "License file missing. Please copy your Risk Frontiers license file in the model_data folder."
        exit 1
    fi

    if [[ ! -f "events.bin" ]]
        then echo "This is not a valid model data directory: events.bin missing"
        exit 1
    fi

    if [[ ! -f "events_p.bin" ]]
        then echo "Creating events_p.bin"
        ln -s events.bin events_p.bin
    fi
    if [[ ! -f "events_h.bin" ]]
        then echo "Creating events_h.bin"
        ln -s events.bin events_h.bin
    fi

    if [[ ! -f "occurrence.bin" ]]
        then echo "This is not a valid model data directory: occurrence.bin missing"
        exit 1
    fi

    if [[ ! -f "occurrence_1.bin" ]]
        then echo "Creating occurrence_1.bin"
        ln -s occurrence.bin occurrence_1.bin
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
