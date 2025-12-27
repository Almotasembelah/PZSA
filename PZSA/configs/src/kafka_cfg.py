from enum import Enum

class TOPICS(Enum):
    RAW_FRAME = 'raw_frame'
    DETECTOR_RESULTS='yolo_results'
    VIOLATION_STATE = 'violation_state'
    USER_INPUTS = 'user_inputs'

class CONFIGS(Enum):
    BOOTSTRAP_SERVER = "127.0.0.1:9092,127.0.0.1:9093"
