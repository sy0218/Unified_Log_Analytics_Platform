#!/bin/bash

# 출력 디렉토리
OUTDIR="/application/node_exporter/textfile_collector"
# 체크할 서비스 목록
SERVICES=("docker" "kafka-server" "zookeeper-server")

# 각 서비스 상태 체크
for service in "${SERVICES[@]}";
do
    OUTFILE="${OUTDIR}/${service}.prom"
    METRIC_NAME="${service//-/_}_up"
    if systemctl is-active --quiet "$service"; then
        echo "$METRIC_NAME 1" > "$OUTFILE"
    else
        echo "$METRIC_NAME 0" > "$OUTFILE"
    fi
done
