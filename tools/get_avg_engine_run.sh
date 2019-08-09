#!/usr/bin/env bash

timestamp=`expr $(echo ${1} | tr -dc '0-9') / 100`
count=0
sum=0
max=0
min=10000
for i in $(cat worker_*_${timestamp:1}*.log | grep "Calculation completed in" | awk -F '[::]' '{print$5}')
do
    sum=`expr ${i} + ${sum}`
    count=`expr ${count} + 1`
    max=$((${max}>${i}?${max}:${i}))
    min=$((${min}>${i}?${i}:${min}))
done
echo avg: `expr ${sum} / ${count}` minutes
echo min: ${min} minutes
echo max: ${max} minutes