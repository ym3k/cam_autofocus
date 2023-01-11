#!/bin/bash
set -e

mkdir -p /opt/cam_autofocus/bin
cp ./gst_start.sh /opt/cam_autofocus/bin

declare -a startsvcs=(\
"gst_start.service"\
)

for v in "${startsvcs[@]}"; do
    cp -i "$v" /etc/systemd/system
    systemctl daemon-reload
    systemctl start "$v"
    systemctl enable "$v"
done
