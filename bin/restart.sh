#!/usr/bin/env bash

basedir="`cd $(dirname $0)/..;pwd`"
cd "$basedir"

./bin/stop.sh
./bin/start.sh
