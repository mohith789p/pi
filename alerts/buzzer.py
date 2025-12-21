import RPi.GPIO as GPIO
import time
import threading
import logging

class Buzzer:
    def __init__(self, gpio, logger=None):
        self.gpio = gpio
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._alarm_thread = None
        self._stop_alarm = threading.Event()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio, GPIO.OUT)
        self.logger.info(f"Buzzer initialized on GPIO {self.gpio}")

    def beep_or_continuous(self, times=None, on_time=0.2, off_time=0.2):
        if times is not None:
            # Short beep mode
            with self._lock:
                try:
                    for _ in range(times):
                        GPIO.output(self.gpio, GPIO.HIGH)
                        time.sleep(on_time)
                        GPIO.output(self.gpio, GPIO.LOW)
                        time.sleep(off_time)
                    self.logger.info(f"Buzzer beeped {times} times")
                except Exception as e:
                    self.logger.error(f"Buzzer beep failed: {e}")
        else:
            # Continuous alarm mode
            if self._alarm_thread and self._alarm_thread.is_alive():
                self.logger.warning("Continuous alarm already running")
                return
            self._stop_alarm.clear()
            self._alarm_thread = threading.Thread(
                target=self._alarm_loop, args=(on_time, off_time), daemon=True
            )
            self._alarm_thread.start()
            self.logger.info("Continuous alarm started")

    def _alarm_loop(self, on_time, off_time):
        try:
            while not self._stop_alarm.is_set():
                with self._lock:
                    GPIO.output(self.gpio, GPIO.HIGH)
                    time.sleep(on_time)
                    GPIO.output(self.gpio, GPIO.LOW)
                    time.sleep(off_time)
        except Exception as e:
            self.logger.error(f"Continuous alarm failed: {e}")

    def stop_alarm(self):
        if self._alarm_thread and self._alarm_thread.is_alive():
            self._stop_alarm.set()
            self._alarm_thread.join()
            with self._lock:
                GPIO.output(self.gpio, GPIO.LOW)
            self.logger.info("Continuous alarm stopped")

    def cleanup(self):
        self.stop_alarm()
        try:
            GPIO.cleanup(self.gpio)
            self.logger.info(f"GPIO {self.gpio} cleaned up")
        except Exception as e:
            self.logger.error(f"GPIO cleanup failed: {e}")
