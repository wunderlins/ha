#!/usr/bin/env bash

export PATH=$PATH:/opt/instantclient_12_1
export ORACLE_HOME=/opt/instantclient_12_1
export LD_LIBRARY_PATH=$ORACLE_HOME
export NLS_LANG="GERMAN_SWITZERLAND.UTF8"

basedir="`cd $(dirname $0)/..;pwd`"
cd "$basedir"

. etc/config.py

nohup ./httpd.py > $web_logfile &
echo $! > op.pid
