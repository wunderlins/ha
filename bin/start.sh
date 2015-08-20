#!/usr/bin/env bash
. etc/config.py

nohup ./httpd.py > $web_logfile &
