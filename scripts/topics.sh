#!/bin/bash
# topics.sh

# The script now points to the service name 'kafka'
BROKER="127.0.0.1:9092"
TOPICS=("raw_frame" "yolo_results" "violation_state" "user_inputs")

for topic in "${TOPICS[@]}"; do
  # Delete if exists (|| true ignores errors if topic doesn't exist)
  docker exec -it $CONTAINER_ID kafka-topics --bootstrap-server $BROKER --delete --topic $topic || true
  # Create topic
   docker exec -it $CONTAINER_ID kafka-topics --bootstrap-server $BROKER --create --topic $topic --replication-factor 1 --partitions 1
done