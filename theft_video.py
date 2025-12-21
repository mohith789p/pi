import cv2
import sys
import yaml
import time
import os
from utils.logger import setup_logger
from inference.detector import Detector
from logic.theft_detector import TheftDetector

# ---------------- CONFIG ----------------
CONFIG_PATH = "config.yaml"
SOURCE = r"D:\Desktop\Projects\Hen_Gaurd\caught.webm"  # absolute path for reliability
WINDOW_NAME = "Theft Detection Demo"
# ----------------------------------------

def main():
    logger = setup_logger()
    try:
        # Load config
        if not os.path.exists(CONFIG_PATH):
            logger.error(f"Config file not found: {CONFIG_PATH}")
            sys.exit(1)

        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)

        if 'model' not in cfg or 'zones' not in cfg:
            logger.error("Config missing 'model' or 'zones' sections")
            sys.exit(1)

        model_cfg = cfg['model']

        # Initialize detector and theft logic
        detector = Detector(model_cfg, logger)
        theft_logic = TheftDetector(cfg['zones'])

        # Video capture
        cap = cv2.VideoCapture(SOURCE)
        if not cap.isOpened():
            logger.error(f"Cannot open video source: {SOURCE}")
            sys.exit(1)

        logger.info(f"Video source opened: {SOURCE}")
        print("Press Q to exit")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning("Failed to read frame or end of video reached")
                break

            # Run detection
            try:
                results = detector.detect(frame)
            except Exception as e:
                logger.error(f"Detection failed: {e}")
                results = None

            humans, hens = [], []

            if results:
                try:
                    if hasattr(results[0], 'boxes') and getattr(results[0].boxes, 'id', None) is not None:
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
                    logger.warning(f"Error processing detection results: {e}")

            # Check theft
            if theft_logic.detect(humans, hens):
                cv2.putText(frame, "THEFT DETECTED!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                logger.warning("🚨 THEFT DETECTED")
                print("🚨 THEFT DETECTED")

            # Display frame (use results[0].plot() if available)
            frame_to_show = frame
            if results:
                try:
                    frame_to_show = results[0].plot()
                except Exception as e:
                    logger.warning(f"Plotting detection results failed: {e}")

            try:
                cv2.imshow(WINDOW_NAME, frame_to_show)
            except Exception as e:
                logger.error(f"Failed to show window: {e}")
                # Save a test frame in case GUI is not available
                cv2.imwrite("debug_frame.jpg", frame_to_show)

            # Wait key (adjust for slower systems)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                logger.info("User requested exit")
                break

        cap.release()
        cv2.destroyAllWindows()
        logger.info("Video processing finished")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
