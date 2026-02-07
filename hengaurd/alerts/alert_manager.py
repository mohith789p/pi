import threading
import time
import logging

class AlertManager:
    def __init__(self, buzzer, gsm, cooldown, logger=None, continuous_alarm=False):
        self.buzzer = buzzer
        self.gsm = gsm
        self.cooldown = cooldown
        self.last_alert_time = 0
        self.continuous_alarm = continuous_alarm
        self.logger = logger or logging.getLogger(__name__)

    def trigger(self, msg):
        if time.time() - self.last_alert_time < self.cooldown:
            self.logger.info("Alert cooldown active. Skipping alert.")
            return
        threading.Thread(target=self._run_alert, args=(msg,), daemon=True).start()

    def _run_alert(self, msg):
        self.logger.info(f"Triggering alert: {msg}")
        buzzer_success = False
        gsm_success = False

        try:
            if self.continuous_alarm:
                self.buzzer.start_alarm()
                buzzer_success = True
            else:
                buzzer_success = self.buzzer.beep()
        except Exception as e:
            self.logger.error(f"Buzzer alert failed: {e}")

        try:
            gsm_success = self.gsm.send_sms(msg)
        except Exception as e:
            self.logger.error(f"GSM alert failed: {e}")

        self.last_alert_time = time.time()

        if buzzer_success and gsm_success:
            self.logger.warning(f"Alert triggered successfully: {msg}")
        elif buzzer_success or gsm_success:
            self.logger.warning(f"Partial alert success: {msg}")
        else:
            self.logger.error(f"Alert failed completely: {msg}")

    def stop_continuous_alarm(self):
        if self.continuous_alarm:
            try:
                self.buzzer.stop_alarm()
                self.logger.info("Continuous alarm stopped")
            except Exception as e:
                self.logger.error(f"Failed to stop continuous alarm: {e}")
