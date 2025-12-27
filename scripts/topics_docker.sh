#!/bin/bash
# topics.sh

# The script now points to the service name 'kafka'
BROKER="kafka:9092"
TOPICS=("raw_frame" "yolo_results" "violation_state" "user_inputs")

for topic in "${TOPICS[@]}"; do
  docker exec kafka kafka-topics --bootstrap-server $BROKER --delete --topic $topic || true
  docker exec kafka kafka-topics --bootstrap-server $BROKER --create --topic $topic --replication-factor 1 --partitions 1
done