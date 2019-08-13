#!/usr/bin/env bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x ${SCRIPT_DIR}/perf_tracker.sh

if  crontab -l | grep -q perf_tracker
then
    crontab -l > mycron
    sed '/perf_tracker/d' ./mycron > mycron_1
    crontab mycron_1
    rm mycron mycron_1
fi
