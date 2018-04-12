#!/usr/bin/env bash
OUT=env.out
echo "Running \"env\" into $OUT"
sleep 5
env > $OUT
echo "DONE!"
