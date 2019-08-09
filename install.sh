#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${SCRIPT_DIR}

# Customize BATCH_COUNT in conf.ini
    SCALE_FACTOR=10 # ideally between 10 and 16 and represents the consumption of memory by the RF .net engine
    BATCH_COUNT=$(expr `awk '/MemFree/ { printf "%.0f \n", $2/1024/1024 }' /proc/meminfo` / ${SCALE_FACTOR})
    BATCH_COUNT=$([ ${BATCH_COUNT} -le 1 ] && echo 1 || echo ${BATCH_COUNT})
    VCPU_COUNT=$(cat /proc/cpuinfo | awk '/^processor/{print $3}' | wc -l)
    BATCH_COUNT=$([ ${VCPU_COUNT} -le ${BATCH_COUNT} ] && echo ${VCPU_COUNT} || echo ${BATCH_COUNT})
    sed -i '/KTOOLS_BATCH_COUNT/c\KTOOLS_BATCH_COUNT = '${BATCH_COUNT} conf.ini

file_docker='docker/Dockerfile'
file_versions='data_version.json'

# Read and set versions 
    env_vars=('OASIS_API_VER' 'OASIS_UI_VER' 'MODEL_VER' 'DATA_VER')
    for var_name in "${env_vars[@]}"; do
            var_value=$(cat ${file_versions} | grep ${var_name} | awk -F'"' '{ print $4 }')
        export ${var_name}=${var_value}
    done

# verify model data and license
MODEL_DATA=${SCRIPT_DIR}/"model_data"
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
cd ${SCRIPT_DIR}

# Arg check 
    if [ $# -eq 0 ]; then
        echo "No arguments provided"
        echo "Required: ./install.sh <MODEL_DATA_STORE>"
        echo "Example:  ./install.sh /Oasis/us-eq/model_data/"
        exit 1
    fi
    export MODEL_DATA_ROOT=$1/${DATA_VER}


# Run API, UI & Worker
    docker-compose -f docker-compose.yml --project-directory $SCRIPT_DIR up -d --build
