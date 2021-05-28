#!/bin/sh
CMD="./speedtest $*"
exec $CMD | tee /var/log/speedtest.json
