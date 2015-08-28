#!/usr/bin/env bash

#for p in `pgrep -f shift.pid`; do
#	kill -TERM $p
#done

kill -TERM `cat op.pid`

