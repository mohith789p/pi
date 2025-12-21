import yaml
import cv2
import sys
import threading
import time

from flask import Flask, Response
from utils.logger import setup_logger
from camera.camera_manager import CameraManager
from inference.detector import Detector
from logic.theft_detector import TheftDetector

# ---------------- GLOBAL SHARED STATE ----------------
latest_frame = None
lock = threading.Lock()
# ----------------------------------------------------

app = Flask(__name__)

def validate_config(cfg):
    required = ['camera', 'model', 'zones']
    for key in required:
        if key not in cfg:
            raise ValueError(f"Missing config key: {key}")

# ---------------- MJPEG STREAM ----------------
def frame_generator():
    while True:
        with lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.01)
            continue

        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )

@app.route("/video")
def video_feed():
    return Response(
        frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
# ----------------------------------------------------

def detection_loop():
    global latest_frame
    logger = setup_logger()

    try:
        with open("config.yaml") as f:
            cfg = yaml.safe_load(f)
        validate_config(cfg)

        camera = CameraManager(cfg["camera"], logger)

        model_cfg = cfg["model"]
        detector = Detector(
            {
                "path": model_cfg.get("path", "models/yolov8n.pt"),
                "conf": model_cfg.get("conf", 0.4),
                "imgsz": model_cfg.get("imgsz", 416),
            },
            logger
        )

        theft_logic = TheftDetector(cfg["zones"])

        while True:
            ret, frame = camera.read()
            if not ret:
                continue

            results = detector.detect(frame)
            humans, hens = [], []

            if results:
                try:
                    if hasattr(results[0], "boxes") and getattr(results[0].boxes, "id", None) is not None:
                        for box in results[0].boxes:
                            tid = int(box.id)
                            cls = int(box.cls)
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                            theft_logic.update_track(tid, cx, cy)

                            if cls == 0:
                                humans.append((tid, (cx, cy)))
                            elif cls == 1:
                                hens.append((cx, cy))
                except Exception as e:
                    logger.warning(f"Detection parse error: {e}")

            if theft_logic.detect(humans, hens):
                logger.info("THEFT DETECTED!")

            output_frame = results[0].plot() if results else frame

            with lock:
                latest_frame = output_frame

    except Exception as e:
        logger.error(f"Fatal detection error: {e}")
        sys.exit(1)

def main():
    # Start detection in background thread
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()

    # Start web server
    app.run(host="0.0.0.0", port=5000, threaded=True)

if __name__ == "__main__":
    main()
