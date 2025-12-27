import cv2
import base64
import numpy as np

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = (boxA[2]-boxA[0]) * (boxA[3]-boxA[1])
    areaB = (boxB[2]-boxB[0]) * (boxB[3]-boxB[1])
    return inter / (areaA + areaB - inter + 1e-6)

def center(box):
    return ((box[0]+box[2])/2, (box[1]+box[3])/2)

def encode_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buffer).decode("utf-8")

def decode_frame(frame):
    frame = base64.b64decode(frame)
    frame = np.frombuffer(frame, np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    return frame

def draw_detections(frame_id, frame, boxes, cls, ids, rois,
                    violation_state, violation_count):

    # initialize persistent state the first time called
    if not hasattr(draw_detections, "violation_until"):
        draw_detections.violation_until = -1

    frame = frame.copy()
    h, w, _ = frame.shape

    # ---------- ROI rectangles ----------
    for ROI in rois:
        x, y, rw, rh = ROI['x'], ROI['y'], ROI['width'], ROI['height']
        cv2.rectangle(frame, (int(x), int(y)), (int(x+rw), int(y+rh)),
                      (255, 0, 0), 2)

    # ---------- VIOLATION DISPLAY LOGIC ----------
    SHOW_FRAMES = 60   # ~2 seconds at 30 FPS

    if violation_state:
        draw_detections.violation_until = frame_id + SHOW_FRAMES

    violation_visible = frame_id <= draw_detections.violation_until

    if violation_visible:
        message = "VIOLATION"

        font_scale = 2.2
        thickness = 3

        (tw, th), _ = cv2.getTextSize(
            message,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            thickness
        )

        # centered at top
        x1 = (w // 2) - (tw // 2)
        y1 = 80

        cv2.rectangle(
            frame,
            (x1 - 12, y1 - th - 12),
            (x1 + tw + 12, y1 + 12),
            (0, 0, 255),
            -1
        )

        cv2.putText(
            frame,
            message,
            (x1, y1),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )

    # ---------- VIOLATION COUNTER ----------
    count_msg = f"Count: {violation_count}"

    (tw, th), _ = cv2.getTextSize(count_msg,
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  1.2, 2)

    x1 = w - tw - 40
    y1 = 110

    cv2.rectangle(
        frame,
        (x1 - 10, y1 - th - 10),
        (x1 + tw + 10, y1 + 10),
        (0, 200, 0),
        -1
    )

    cv2.putText(
        frame,
        count_msg,
        (x1, y1),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 0),
        2,
        cv2.LINE_AA
    )

    CLASS_COLORS = {
            "hand":   (0, 255, 255),   # yellow
            "person": (0, 165, 255),   # orange
            "scooper":(255, 0, 0),     # blue
            "pizza":  (0, 255, 0),     # green
        }

    # ---------- DRAW OBJECTS ----------
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)

        class_label = cls[i]
        obj_id = ids[i] if ids else -1

        color = CLASS_COLORS[class_label]

        label = (
            f"{class_label} ID:{obj_id}"
            if obj_id != -1 and ids
            else f"{class_label}"
        )

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        (tw, th), _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            2
        )

        cv2.rectangle(
            frame,
            (x1, y1 - th - 6),
            (x1 + tw + 6, y1),
            color,
            -1
        )

        cv2.putText(
            frame,
            label,
            (x1 + 3, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )

    return encode_frame(frame)
