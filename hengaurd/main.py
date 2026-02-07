import os
import yaml
import cv2
import sys
from utils.logger import setup_logger
from camera.camera_manager import CameraManager
from inference.detector import Detector
from logic.theft_detector import TheftDetector
from alerts.buzzer import Buzzer
from alerts.gsm_manager import SIM900
from alerts.alert_manager import AlertManager

def validate_config(cfg):
    required = ['camera', 'model', 'zones', 'alerts']
    for key in required:
        if key not in cfg:
            raise ValueError(f"Missing config key: {key}")
    alerts_cfg = cfg['alerts']
    for key in ['buzzer_gpio', 'gsm', 'cooldown']:
        if key not in alerts_cfg:
            raise ValueError(f"Missing alert config key: {key}")

def main():
    logger = setup_logger()
    try:
        with open("config.yaml") as f:
            cfg = yaml.safe_load(f)
        validate_config(cfg)

        camera = CameraManager(cfg['camera'], logger)

        model_cfg = cfg['model']
        model_path = model_cfg.get('path', 'models/yolov8n.pt')

        if not os.path.exists(model_path):
            logger.warning(
                f"Model file '{model_path}' not found. Falling back to pretrained yolov8n.pt"
            )
            model_path = 'yolov8n.pt'

        detector = Detector(
            {
                "path": model_path,
                "conf": model_cfg.get("conf", 0.4),
                "imgsz": model_cfg.get("imgsz", 416)
            },
            logger
        )

        theft_logic = TheftDetector(cfg['zones'])
        buzzer = Buzzer(cfg['alerts']['buzzer_gpio'], logger)
        gsm = SIM900(cfg['alerts']['gsm'])

        continuous_alarm = cfg['alerts'].get('continuous_alarm', False)
        alert_mgr = AlertManager(
            buzzer, gsm, cfg['alerts']['cooldown'], logger, continuous_alarm=continuous_alarm
        )

        while True:
            if camera.camera_offline_too_long:
                alert_mgr.trigger("CAMERA OFFLINE TOO LONG")

            ret, frame = camera.read()
            if not ret:
                continue

            results = detector.detect(frame)
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

            if theft_logic.detect(humans, hens):
                alert_mgr.trigger("HEN THEFT DETECTED")

            cv2.imshow("THEFT DETECTION", results[0].plot() if results else frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        try:
            camera.release()
        except Exception:
            pass
        try:
            if continuous_alarm:
                buzzer.stop_alarm()
        except Exception:
            pass
        try:
            buzzer.cleanup()
        except Exception:
            pass
        try:
            gsm.cleanup()
        except Exception:
            pass
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
