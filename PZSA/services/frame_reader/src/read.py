import cv2
import base64
import json
import time
from confluent_kafka import Producer, Consumer, KafkaException

from PZSA.configs import TOPICS, CONFIGS, logger


def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.debug(
            f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )


class FrameReader:
    def __init__(self):
        # Producer
        self.producer = Producer({
            "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
            "message.max.bytes": 10485760  # 10MB
        })

        # Consumer
        self.consumer = Consumer({
            "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
            "group.id": "frame-reader",
            "auto.offset.reset": "earliest",
        })

        self.consumer.subscribe([TOPICS.USER_INPUTS.value])

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buffer).decode("utf-8")

    def read_and_publish(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            data = json.loads(msg.value().decode("utf-8"))
            vid_source = data["vid_source"]
            logger.info(f"Received video source: {vid_source}")

            cap = cv2.VideoCapture(vid_source)

            if not cap.isOpened():
                logger.error(f"Failed to open video source: {vid_source}")
                continue

            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
            frame_id = 0

            logger.info(f"Starting frame reading from {vid_source}")

            try:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        logger.info("End of video stream")
                        break

                    encoded = self.encode_frame(frame)

                    message = {
                        "frame_id": frame_id,
                        "frame": encoded
                    }
                    self.producer.produce(
                        topic=TOPICS.RAW_FRAME.value,
                        value=json.dumps(message).encode("utf-8"),
                        callback=delivery_report,
                    )

                    # Serve delivery callbacks
                    self.producer.poll(0)
                    logger.info(f"Reading and Sending Frame {frame_id}")
                    frame_id += 1
                    time.sleep(1.0 / fps)

            finally:
                cap.release()
                self.producer.flush()
                logger.info(f"Processed {frame_id} frames")


if __name__ == "__main__":
    reader = FrameReader()
    reader.read_and_publish()
