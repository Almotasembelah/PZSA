from confluent_kafka import Producer, Consumer, KafkaException
from flask import request, Blueprint, Response

from PZSA.configs import TOPICS, CONFIGS

import json
import tempfile
import time

stream_blueprint = Blueprint('stream', __name__)


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


producer = Producer({
    "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
    "message.max.bytes": 10485760
})


@stream_blueprint.route('/process', methods=['POST'])
def process():

    video_file = request.files.get('video')
    rois_json = request.form.get('rois')
    rois = json.loads(rois_json)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        video_file.save(tmp.name)
        temp_video_path = tmp.name

    msg = {"vid_source": temp_video_path, "rois": rois}

    producer.produce(
        topic=TOPICS.USER_INPUTS.value,
        key="latest".encode("utf-8"),
        value=json.dumps(msg).encode("utf-8"),
        callback=delivery_report
    )
    producer.flush()

    consumer = Consumer({
        "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
        "group.id": f"stream-service-{time.time_ns()}",
        "auto.offset.reset": "latest",
        "enable.auto.commit": True
    })
    consumer.subscribe([TOPICS.VIOLATION_STATE.value])

    def stream_frames():
        try:
            while True:
                msg = consumer.poll(1.0)
                if not msg:
                    continue

                data = json.loads(msg.value())
                print('Inside stream, streaming frame: ', data['frame_id'])
                yield "data: " + json.dumps({
                    "type": "frame",
                    "frame_data": data["frame"]
                }) + "\n\n"

        finally:
            consumer.close()

    return Response(
        stream_frames(),
        mimetype="text/event-stream"
    )