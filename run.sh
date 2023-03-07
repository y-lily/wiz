#!/bin/sh
log="log.txt"
time_format="\nTime: %E \nAvg CPU: %P \nMax set size: %M KB \nAvg Mem: %K KB"

echo "start: $(date)" >> $log
source .venv/bin/activate
/usr/bin/time --format="$time_format" -a -o $log strace -c -A -o $log python main.py
echo >> log.txt
deactivate
