from confluent_kafka import Producer, Consumer, KafkaException
import json
from datetime import datetime

from .utils import iou, draw_detections, decode_frame
from PZSA.configs import TOPICS, CONFIGS, logger
from PZSA.services.controller import ViolationController
from PZSA.data import DatabaseManager

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
    # no-op on success (avoid overhead during streaming)


class ViolationDetector:
    def __init__(self):
        logger.info("Initializing ViolationDetector...")

        # Producer
        self.producer = Producer({
            "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
            "message.max.bytes": 10485760
        })

        # Consumer
        self.consumer = Consumer({
            "bootstrap.servers": CONFIGS.BOOTSTRAP_SERVER.value,
            "group.id": "violation-service",
            "auto.offset.reset": "earliest",
        })

        self.consumer.subscribe([TOPICS.DETECTOR_RESULTS.value, TOPICS.USER_INPUTS.value])
        
        self.first_frame_index = None
        self.last_frame_index = None
        self.hand_memory = {}
        self.rois = None
        self.violation_count = 0

        db_manager = DatabaseManager()
        self.controller = ViolationController(db_manager=db_manager)

        logger.info("ViolationDetector initialized successfully.")

    def in_roi(self, box, roi):
        """
        Check if a bounding box is inside a region of interest.
        """
        return iou(box, roi) > 0.2

    def check_violation(self, data):
        """
        Check for violations in the given frame data.
        Returns a dictionary containing:
        - frame: annotated frame
        - violation_state: bool
        - violation_count: total violations detected
        - first_frame_index, last_frame_index: frame indices for the violation
        - frame_id: current frame index
        """
        frame_data = data['frame_data']
        frame = frame_data['frame']
        frame_idx = frame_data['frame_id']
        logger.info(f"Checking violations for frame {frame_idx}")

        detection_data = data['detection']
        bboxes = detection_data['boxes']
        cls = detection_data['cls']
        ids = detection_data['ids']

        hands, scoopers, pizza = [], [], []

        for i, b in enumerate(bboxes):
            box_result = {'bbox': b, 'id': ids[i]}
            if cls[i] == 'hand':
                hands.append(box_result)
            elif cls[i] == 'scooper':
                scoopers.append(box_result)
            elif cls[i] == 'pizza':
                pizza.append(box_result)

        violation_state = False

        for hand in hands:
            has_scooper = any(iou(hand['bbox'], s['bbox']) > 0.1 for s in scoopers)

            for ROI in self.rois:
                x, y, w, h = ROI['x'], ROI['y'], ROI['width'], ROI['height']
                ROI_box = [x, y, x+w, y+h]
                if self.in_roi(hand['bbox'], ROI_box):
                    self.hand_memory[hand['id']] = (has_scooper, frame_idx)
                    if not has_scooper and self.first_frame_index is None:
                        self.first_frame_index = frame_idx

            if any(iou(hand['bbox'], p['bbox']) > 0.1 for p in pizza):
                used_scooper, no_scooper_frame_id = self.hand_memory.get(hand['id'], (True, -1))
                if not used_scooper and (frame_idx >= no_scooper_frame_id+30 and no_scooper_frame_id != -1):
                    violation_state = True
                    self.last_frame_index = frame_idx
                    self.violation_count += 1
                    self.hand_memory[hand['id']] = (True, -1)
                    logger.info(f"Violation detected at frame {frame_idx} for hand {hand['id']}")

        frame = decode_frame(frame)
        frame = draw_detections(frame_idx, frame, bboxes, cls, ids, self.rois, violation_state, self.violation_count)

        result = {
            'frame': frame,
            'violation_state': violation_state,
            'violation_count': self.violation_count,
            'first_frame_index': self.first_frame_index,
            'last_frame_index': self.last_frame_index,
            'frame_id': frame_idx
        }
        
        if violation_state:
            self.last_frame_index, self.first_frame_index = None, None
            self.hand_memory = {}
        
        return result

    def process(self):
        """
        Main loop to process Kafka messages, check for violations,
        produce results, and save violations to the database.
        """
        logger.info("Starting ViolationDetector process loop...")
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                raise KafkaException(msg.error())
            
            topic = msg.topic()
            data = json.loads(msg.value().decode("utf-8"))

            if topic == TOPICS.USER_INPUTS.value:
                self._reset()
                self.rois = data.get('rois')
                logger.info(f"Received new ROIs: {self.rois}")

            elif topic == TOPICS.DETECTOR_RESULTS.value:
                if self.rois is None:
                    continue

                result_msg = self.check_violation(data)

                self.producer.produce(
                    topic=TOPICS.VIOLATION_STATE.value,
                    value=json.dumps(result_msg).encode("utf-8"),
                    callback=delivery_report
                )
                self.producer.poll(0)

                if result_msg['violation_state']:
                    timestamp = datetime.utcnow()
                    frame_path = self.controller.save_frame(decode_frame(result_msg['frame']), timestamp=timestamp)
                    violation_data = {
                        'frame_path': frame_path,
                        'first_frame_index': result_msg['first_frame_index'],
                        'last_frame_index': result_msg['last_frame_index'],
                        'boxes': data['detection']['boxes'],
                        'labels': data['detection']['cls'],
                        'timestamp': timestamp
                    }
                    self.controller.create_violation(**violation_data)
                    self.controller.save_to_db()
                    logger.info(f"Violation saved to DB at frame {result_msg['frame_id']}")

    def _reset(self):
        """
        Reset internal state for a new session or new ROIs.
        """
        logger.info("Resetting ViolationDetector internal state...")
        self.first_frame_index = None
        self.last_frame_index = None
        self.hand_memory = {}
        self.rois = None
        self.violation_count = 0
        self.controller.delete_databse()
        logger.info("Reset complete.")


if __name__=='__main__':
    checker = ViolationDetector()
    checker.process()