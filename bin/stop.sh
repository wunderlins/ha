#!/usr/bin/env bash

#for p in `pgrep -f shift.pid`; do
#	kill -TERM $p
#done

basedir="`cd $(dirname $0)/..;pwd`"
cd "$basedir"

kill -TERM `cat op.pid`

