#!/usr/bin/env bash

for p in `pgrep -f httpd.py`; do
	kill -TERM $p
done

rm -R var/session_*
