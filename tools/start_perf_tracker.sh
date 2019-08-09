#!/usr/bin/env bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x ${SCRIPT_DIR}/perf_tracker.sh

if  ! crontab -l | grep -q perf_tracker
then
    crontab -l > mycron
    echo "*/1 * * * * ${SCRIPT_DIR}/perf_tracker.sh >> ${SCRIPT_DIR}/perf.csv" >> mycron
    crontab mycron
    rm mycron
fi
