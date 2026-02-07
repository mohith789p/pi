from ultralytics import YOLO
import os
import time

class Detector:

    def __init__(self, cfg, logger, alert_callback=None, max_failures=10, inference_warn_ms=200):
        self.logger = logger
        self.alert_callback = alert_callback
        self.max_failures = max_failures
        self.inference_warn_ms = inference_warn_ms
        self.failure_count = 0

        model_path = cfg['path']
        ext = os.path.splitext(model_path)[1].lower()
        if ext != '.pt':
            self.logger.error(
                f"Model format {ext} not supported. Use .pt weights with Ultralytics YOLO(). "
                "ONNX is not supported directly. Convert ONNX to .pt using Ultralytics export tools."
            )
            raise ValueError("Unsupported model format for Ultralytics YOLO. Use .pt weights.")

        if cfg['imgsz'] > 416:
            self.logger.warning(
                "imgsz > 416 may cause slow inference on Raspberry Pi. "
                "Use yolov8n.pt and imgsz <= 320 for best performance."
            )

        try:
            self.model = YOLO(model_path)
            self.conf = cfg['conf']
            self.imgsz = cfg['imgsz']
            self.logger.info(
                "Model loaded. For Pi, use yolov8n.pt and imgsz <= 320 for best speed. "
                "Monitor memory if using persist=True."
            )
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            raise

    def detect(self, frame):
        if frame is None:
            self.logger.warning("Detector received None frame. Skipping detection.")
            self.failure_count += 1
            self._maybe_alert_failure()
            return []

        start = time.time()
        try:
            results = self.model.track(
                frame,
                persist=True,
                conf=self.conf,
                imgsz=self.imgsz,
                verbose=False
            )
            elapsed_ms = (time.time() - start) * 1000
            if elapsed_ms > self.inference_warn_ms:
                self.logger.warning(
                    f"Detection inference time {elapsed_ms:.1f}ms exceeds {self.inference_warn_ms}ms. "
                    "Consider reducing imgsz or using a smaller model."
                )
            if (
                not results or
                not hasattr(results[0], 'boxes') or
                not hasattr(results[0].boxes, 'id')
            ):
                self.logger.warning(
                    "Detection returned no results or malformed results (missing boxes or id). Skipping frame."
                )
                self.failure_count += 1
                self._maybe_alert_failure()
                return []
            self.failure_count = 0
            return results
        except Exception as e:
            self.logger.error(f"Detection failed: {e}")
            self.failure_count += 1
            self._maybe_alert_failure()
            return []

    def _maybe_alert_failure(self):
        if self.failure_count >= self.max_failures:
            msg = (
                f"Detection pipeline offline: {self.failure_count} consecutive failures. "
                "Check model, input, or hardware."
            )
            self.logger.error(msg)
            if self.alert_callback:
                self.alert_callback(msg)