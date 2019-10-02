#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${SCRIPT_DIR}

GLOBAL_LICENCE_PATH=""

function compute_batch_count()
{
    scale_factor=$1
    MEM_SIZE=$(awk '/MemTotal/ { printf "%.0f \n", $2/1024/1024 }' /proc/meminfo)
    # batch_count=$(expr  ${MEM_SIZE}/ ${scale_factor})
    # batch_count=$([ ${batch_count} -le 1 ] && echo 1 || echo ${batch_count})
    # VCPU_COUNT=$(cat /proc/cpuinfo | awk '/^processor/{print $3}' | wc -l)
    # batch_count=$([ ${VCPU_COUNT} -le ${batch_count} ] && echo ${VCPU_COUNT} || echo ${batch_count})
    batch_count=$([ ${MEM_SIZE} -le 128 ] && echo 2 || echo 4)
    echo ${batch_count}
}


function valid_licence()
{
    # TODO: this needs to be able to do some parsing of the license file rather that this simplistic check
    if [[ -f $1 ]]
    then
        return 0 # success
    else
        return 1 # failure
    fi
}

function set_new_licence()
{
    read -p "Please set path to the Risk Frontiers licence file [$1]: " licence_path_in
    if [[ ! -f ${licence_path_in} ]]
    then
        echo "Licence file not found in ${licence_path_in}. Exiting now!"
        exit 1
    fi
    GLOBAL_LICENCE_PATH=${licence_path_in}
}


file_docker='docker/Dockerfile'
file_versions='data_version.json'

# Read and set versions
env_vars=('OASIS_API_VER' 'OASIS_UI_VER' 'MODEL_VER' 'DATA_VER' 'INTEGRATION_VER' 'KTOOLS_VER' 'OASISLMF_VER')
for var_name in "${env_vars[@]}"; do
        var_value=$(cat ${file_versions} | grep ${var_name} | awk -F'"' '{ print $4 }')
    export ${var_name}=${var_value}
done
echo "
#########################################################################
 Welcome to the Risk Frontiers HailAUS ${MODEL_VER} Oasis Integration ${INTEGRATION_VER}.
 This release was developed and validated with the following components:

   Model Data: ${DATA_VER}
   Oasis API: ${OASIS_API_VER}
   Oasis UI: ${OASIS_UI_VER}
   Oasislmf: ${OASISLMF_VER}
   Ktools: ${KTOOLS_VER}

#########################################################################
"

echo "Installation started. Please follow the following instruction and press ENTER to use the suggested default values"

# Customize BATCH_COUNT in conf.ini
# SCALE_FACTOR is ideally between 10 and 16 and represents the consumption of memory by the RF .net engine
MIN_SCALE_FACTOR=10
MAX_SCALE_FACTOR=20
min_batch_count=1  # $(compute_batch_count ${MAX_SCALE_FACTOR})
max_batch_count=$(compute_batch_count ${MIN_SCALE_FACTOR})

batch_count=${max_batch_count}
read -p "Please set KTOOLS_BATCH_COUNT (ideally between ${min_batch_count} and ${max_batch_count}) [${batch_count}]: " batch_count_in
re='^[0-9]+$'
if [[ ! -z ${batch_count_in} ]] && [[ ${batch_count_in} =~ $re ]]
then
    batch_count=${batch_count_in}
fi
sed -i '/KTOOLS_BATCH_COUNT/c\KTOOLS_BATCH_COUNT = '${batch_count} conf.ini
echo "Updated 'KTOOLS_BATCH_COUNT' in conf.ini to ${batch_count}"

# set model data path
model_data=${SCRIPT_DIR}/model_data
read -p "Please enter the place where model data was downloaded (ABSOLUTE PATH) [${model_data}]: " model_data_in
if [[ ! -z ${model_data_in} ]]
then
    model_data=${model_data_in}/${DATA_VER}
else
    model_data=${model_data}/${DATA_VER}
fi
export MODEL_DATA_ROOT=${model_data}

# verify model data and licence
if [[ -d ${model_data} ]]
    then cd ${model_data}

    # shallow verify licence
    licence_path=${model_data}/licence.txt
    if [[ ! -f license.txt ]] && [[ ! -f licence.txt ]]
    then
        set_new_licence ${licence_path}
        licence_path=${GLOBAL_LICENCE_PATH}
    else
        licence_path=$([ -f ${model_data}/licence.txt ] && echo ${model_data}/licence.txt || echo ${model_data}/license.txt)
        read -p "Licence file exists in ${licence_path}. Do you want to use it? [Y]: " confirm_licence
        if [[ ! -z ${confirm_license} ]] && [[ ! ${confirm_licence} = "Y" ]] && [[ ! ${confirm_licence} = "y" ]]
        then
             set_new_licence ${licence_path}
             licence_path=${GLOBAL_LICENCE_PATH}
        fi
    fi
    if  ! valid_licence ${licence_path}
    then
        echo "Licence file is invalid. Exiting now!"
        exit 1
    fi

    cp ${licence_path} /tmp/licence.txt; cp /tmp/licence.txt ${model_data}; rm /tmp/licence.txt
    echo "Licence file installed in ${model_data}"

    # shallow verify model_data
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
    echo "The model data '${model_data}' does not exist"
    exit 1
fi

cd ${SCRIPT_DIR}
# Run API, UI & Worker
read -r -p "Do you want to build worker docker image locally? [y/N]: " response
response=${response,,}    # to lower
if [[ "$response" =~ ^(yes|y)$ ]]
then
    docker-compose -f docker-compose.yml --project-directory ${SCRIPT_DIR} up -d --build
else
    docker-compose -f docker-compose.nobuild.yml --project-directory ${SCRIPT_DIR} up -d --build
fi
