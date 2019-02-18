#!/usr/bin/env bash
OUT=env.out
echo "Running \"env\" into $OUT"
sleep 5
/bin/env > $OUT
/bin/ls
echo "DONE!"
