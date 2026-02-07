import cv2
import time

class CameraManager:
    def __init__(self, cfg, logger, max_failures=5, offline_alert_seconds=30, max_backoff=60):
        self.logger = logger
        self.cfg = cfg
        self.max_failures = max_failures
        self.failure_count = 0
        self.is_alive = False
        self.cap = None
        self.last_alive_time = time.time()
        self.offline_alert_seconds = offline_alert_seconds
        self.max_backoff = max_backoff
        self._backoff = 1
        self._init_camera()

    def _init_camera(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        try:
            self.cap = cv2.VideoCapture(self.cfg['source'])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg['width'])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg['height'])
            self.cap.set(cv2.CAP_PROP_FPS, self.cfg['fps'])
            if not self.cap.isOpened():
                self.logger.error("Camera init failed: Unable to open camera source.")
                self.is_alive = False
                raise RuntimeError("Camera init failed")
            # Verify actual camera properties
            actual_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.logger.info(f"Camera initialized. Actual properties: width={actual_w}, height={actual_h}, fps={actual_fps}")
            self.is_alive = True
            self.failure_count = 0
            self.last_alive_time = time.time()
            self._backoff = 1
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            self.is_alive = False

    def read(self):
        if not self.is_alive:
            self.logger.error(f"Camera is not alive. Read aborted. Backing off for {self._backoff} seconds.")
            time.sleep(self._backoff)
            self._backoff = min(self._backoff * 2, self.max_backoff)
            self._init_camera()
            return False, None
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.failure_count += 1
                self.logger.warning(f"Camera read failed: No frame captured. Failure count: {self.failure_count}")
                if self.failure_count >= self.max_failures:
                    self.logger.error("Max consecutive camera failures reached. Attempting reinitialization.")
                    self.is_alive = False
                    self._init_camera()
                return False, None
            self.failure_count = 0
            self.last_alive_time = time.time()
            self._backoff = 1
            return ret, frame
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Camera read exception: {e}. Failure count: {self.failure_count}")
            if self.failure_count >= self.max_failures:
                self.logger.error("Max consecutive camera failures reached. Attempting reinitialization.")
                self.is_alive = False
                self._init_camera()
            return False, None

    @property
    def camera_offline_too_long(self):
        if not self.is_alive and (time.time() - self.last_alive_time) > self.offline_alert_seconds:
            return True
        return False

    def release(self):
        try:
            if self.cap is not None:
                self.cap.release()
                self.logger.info("Camera released.")
        except Exception as e:
            self.logger.error(f"Camera release exception: {e}")
        self.is_alive = False