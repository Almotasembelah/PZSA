from ioutrack import Sort
from ultralytics import YOLO
import ultralytics.trackers.bot_sort as bot_sort

from confluent_kafka import Producer, Consumer, KafkaException

import json
import base64
import cv2
import numpy as np

from PZSA.configs import TOPICS, CONFIGS, logger


def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Kafka delivery failed: {err}")

#########################################################################
# https://github.com/Y-T-G/ioutrack_rs
# Monkey-patch Rust-based tracker
def update(self, dets, *args, **kwargs):
    boxes, cls = dets.data[:, :5], dets.data[:, -1:]
    tracks = tracker.update(boxes, return_indices=True)
    idxs = tracks[:, -1:].astype(int)
    confs = boxes[idxs.flatten(), 4:5]
    tracks = np.hstack((tracks[:, :-1], confs, cls[idxs.flatten()], idxs))
    return tracks


tracker = Sort(max_age=20, min_hits=2, init_tracker_min_score=0.2)
bot_sort.BOTSORT.update = update
##########################################################################

class Detector:
    """
    Detector Service

    This service receives frames from the `frame_reader` microservice via Kafka,
    performs object detection and tracking, and publishes enriched detection
    results to the `violation_checker` service.

    Two detection models are used:

    1) Custom model  
       Detects: hands, scooper, pizza  
       However, detections are not always persistent across frames, which causes
       unstable tracking IDs.

    2) Pre-trained YOLO person detector  
       Detects persons with high temporal stability.
       The nearest detected person is assigned to each detected hand,
       providing a stable hand-to-worker identity mapping.

    This ensures that both hands belonging to the same worker share
    the same track ID, which is required for the violation logic.

    The service runs continuously and processes frames in real-time.
    """

    def __init__(self, model_path: str):
        """
        Initialize detector service components.

        Loads:
        - custom detection model
        - stable person detector
        - Kafka consumer and producer
        - class decoding map
        """

        logger.info("Initializing Detector service")

        self.model = YOLO(model_path)
        self.person_detector = YOLO("yolo11s.pt")

        # Kafka Producer
        self.producer = Producer({
            "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
            "message.max.bytes": 10485760
        })

        # Kafka Consumer
        self.consumer = Consumer({
            "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
            "group.id": "detector-service",
            "auto.offset.reset": "earliest",
        })

        self.consumer.subscribe([TOPICS.RAW_FRAME.value])

        # class id mapping for custom model
        self.cls_decode = {0: "hand", 2: "pizza", 3: "scooper"}

        logger.info("Detector service initialized successfully")

    def track(self):
        """
        Start receiving frames and running detection + tracking.

        Processing steps:

        1) receive frame from Kafka
        2) decode and convert image
        3) reset model state when a new video starts
        4) detect persons (stable tracking IDs)
        5) detect hands / scooper / pizza (custom model)
        6) re-assign hands to nearest person
        7) publish merged detection output

        This method runs continuously.
        """

        logger.info("Detector processing loop started")

        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            data = json.loads(msg.value().decode("utf-8"))

            frame_id = data["frame_id"]

            # Reset tracker for new video stream
            if frame_id == 0:
                self._reset()
                logger.info("Tracker reset for new video sequence")

            # decode frame
            frame_encoded = data["frame"]
            jpg_bytes = base64.b64decode(frame_encoded)
            np_arr = np.frombuffer(jpg_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # Person detection (stable IDs)
            person_detection = self.person_detector.track(
                frame,
                tracker="btrack.yaml",
                conf=0.6,
                verbose=False,
                persist=True
            )

            # Custom detection
            results = self.model.predict(frame, conf=0.1, verbose=False)

            detections = self.get_results(results[0], person_detection[0])

            result_msg = {
                "detection": detections,
                "frame_data": data
            }

            logger.info(f"Processed frame {frame_id}")

            self.producer.produce(
                topic=TOPICS.DETECTOR_RESULTS.value,
                value=json.dumps(result_msg).encode("utf-8"),
                callback=delivery_report
            )

            self.producer.poll(0)

    def get_results(self, custom_detection, coco_detection):
        """
        Combine detections from both models.

        - Filters out person detections from the custom model
        - Keeps custom detections: hand, scooper, pizza
        - Uses YOLO person detector for stable person tracking
        - Assigns each hand to the closest detected person
        """

        _cls = custom_detection.boxes.cls
        mask = _cls != 1.0   # ignore "person" class in custom model

        boxes = custom_detection.boxes.xyxy[mask].detach().cpu().numpy()
        cls = custom_detection.boxes.cls[mask].detach().cpu().numpy()
        id = np.array([-1] * len(boxes), dtype=np.float16)

        cls_coco = coco_detection.boxes.cls
        mask = cls_coco == 0  # keep only persons

        persons_boxes = coco_detection.boxes.xyxy[mask].detach().cpu().numpy().tolist()
        persons_cls = ["person"] * len(persons_boxes)

        if coco_detection.boxes.id is not None:
            persons_id = coco_detection.boxes.id[mask].detach().cpu().numpy().tolist()

            # assign each hand to nearest person
            hands_mask = cls == 0.0
            hands_boxes = boxes[hands_mask].tolist()

            new_ids = self._assign_hands2persons(hands_boxes, persons_boxes, persons_id)

            id[hands_mask] = new_ids

        else:
            persons_id = [-1] * len(persons_boxes)

        id = id.tolist()
        cls = [self.cls_decode[int(c)] for c in cls]
        boxes = boxes.tolist()

        # merge detections
        boxes.extend(persons_boxes)
        cls.extend(persons_cls)
        id.extend(persons_id)

        return {"boxes": boxes, "cls": cls, "ids": id}

    def _assign_hands2persons(self, hands, persons, person_id):
        """
        Assign each detected hand to the closest person
        using Euclidean distance between bounding box centers.

        Returns
        -------
        list[int]
            List of assigned person IDs aligned to hand detections.
        """

        ids_ls = []

        if len(persons) > 0 and len(hands) > 0:
            for hand in hands:
                hand = self._center(hand)

                distances = [
                    (self._dist(hand, self._center(person)), person_id[i])
                    for i, person in enumerate(persons)
                ]

                _, pid = min(distances, key=lambda x: x[0])
                ids_ls.append(pid)

        return ids_ls

    def _center(self, box):
        """Return bounding box center as (x, y)."""
        return [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]

    def _dist(self, a, b):
        """Compute Euclidean distance between two points."""
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def _reset(self):
        """
        Reset the person detector to clear tracking history.

        This is triggered when a new video stream begins.
        """
        logger.info("Resetting person detector and clearing track history")
        self.person_detector = YOLO("yolo11s.pt")


if __name__ == "__main__":
    detector = Detector("./resources/model/yolo12m-v2.pt")
    detector.track()
