import serial
import time
import logging

class SIM900:
    def __init__(self, cfg, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.phone = cfg['phone']
        try:
            self.ser = serial.Serial(cfg['port'], cfg['baud'], timeout=1)
            self.logger.info("SIM900 initialized")
        except Exception as e:
            self.logger.error(f"Failed to open serial port: {e}")
            raise
        
        if not self._send("AT"):
            self.logger.warning("SIM900 not responding to AT")
        if not self._send("AT+CMGF=1"):
            self.logger.warning("Failed to set SMS text mode")

    def _send(self, cmd, wait="OK", timeout=5):
        try:
            self.ser.reset_input_buffer()
            self.ser.write((cmd + "\r\n").encode())
            end = time.time() + timeout
            resp = ""
            while time.time() < end:
                n = self.ser.in_waiting
                if n:
                    resp += self.ser.read(n).decode(errors='ignore')
                    if wait in resp:
                        return True
                time.sleep(0.05)
            self.logger.warning(f"No response for command '{cmd}'")
            return False
        except Exception as e:
            self.logger.error(f"Error sending command '{cmd}': {e}")
            return False

    def send_sms(self, msg, retries=3):
        for attempt in range(1, retries + 1):
            if self._send(f'AT+CMGS="{self.phone}"', wait=">"):
                self.ser.write((msg + "\x1A").encode())
                self.logger.info(f"SMS sent on attempt {attempt}")
                time.sleep(1)  # allow modem to process
                return True
            else:
                self.logger.warning(f"SMS attempt {attempt} failed")
                time.sleep(1)
        self.logger.error("All SMS attempts failed")
        return False

    def make_call(self, duration=10):
        """Auto call, hang up after duration"""
        if self._send(f'ATD{self.phone};'):
            self.logger.info("Call started")
            time.sleep(duration)
            self._send("ATH")
            self.logger.info("Call ended")
        else:
            self.logger.error("Failed to start call")

    def cleanup(self):
        try:
            self.ser.close()
            self.logger.info("SIM900 serial port closed")
        except Exception as e:
            self.logger.error(f"Failed to close SIM900 serial port: {e}")
