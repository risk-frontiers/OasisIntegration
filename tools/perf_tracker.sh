#!/usr/bin/env bash

timestamp=$(date +'%d-%m-%y %H:%M:%S')
disk_os=$(awk '/^\/dev/ {printf("%s", $3);}' <(df -h /))
disk_mnt=$(awk '/^\/dev/ {printf("%s", $3);}' <(df -h /mnt))
used_mem=$(awk '/^Mem/ {printf("%s", $3);}' <(free -h))
free_mem=$(awk '/^Mem/ {printf("%s", $4);}' <(free -h))
cache_mem=$(awk '/^Mem/ {printf("%s", $6);}' <(free -h))
cpu=$(top -b -n2 | grep "Cpu(s)" | awk '{print $2+$4 "%"}' | tail -n1)
echo ${timestamp},${disk_os},${disk_mnt},${used_mem},${cache_mem},${free_mem},${cpu}