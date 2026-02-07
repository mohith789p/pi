# HenGuard – Intelligent Poultry Theft Detection System

HenGuard is a Raspberry Pi–based computer vision and alerting system designed to detect poultry theft in real time using a camera, YOLOv8 object detection, motion analysis, and GSM-based alerts.

---

## System Overview

The system follows a strict separation of concerns:

- **Camera Layer** – Captures frames from the Pi Camera
- **Inference Layer** – Runs YOLOv8 detection and tracking
- **Logic Layer** – Analyzes motion + proximity to infer theft
- **Alert Layer** – Triggers buzzer and GSM alerts asynchronously

This architecture avoids blocking the vision loop and ensures long-term reliability.

---

## Features

- Real-time human and hen detection
- Motion-based theft inference (time-normalized velocity)
- Configurable thresholds via `config.yaml`
- Non-blocking alerts (threaded GSM + buzzer)
- Designed for continuous unattended operation

---

## Hardware Requirements

- Raspberry Pi 4 (recommended)
- Pi Camera Module / USB Camera
- SIM900 GSM Module
- Active SIM card
- Buzzer
- External power supply (important for GSM stability)

---

## Software Requirements

- Raspberry Pi OS (64-bit recommended)
- Python 3.8+
- Internet access (for initial setup)

---

## Directory Structure

```
henguard/
├── main.py
├── config.yaml
├── camera/
│   └── camera_manager.py
├── inference/
│   └── detector.py
├── logic/
│   └── theft_detector.py
├── alerts/
│   ├── alert_manager.py
│   ├── buzzer.py
│   └── gsm_manager.py
├── utils/
│   ├── fs.py
│   └── logger.py
└── logs/
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd henguard
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure the system

Edit `config.yaml` to set:

- Camera parameters
- Model path and confidence
- GSM port, baud rate, phone number
- Theft thresholds and alert cooldown

---

## Running the System

```bash
python3 main.py
```

Press `q` to exit (for development mode).

---

## Deployment (Recommended)

For production use:

- Disable GUI rendering
- Run as a `systemd` service
- Enable auto-restart on failure

---

## Important Notes

- Model training should be done on a PC or cloud, **not on the Pi**
- Use ONNX models for better performance on Raspberry Pi
- Stable power is critical for GSM reliability

---

## Limitations

- Accuracy depends heavily on dataset quality
- Poor lighting conditions may affect detection
- GSM alerts depend on network availability

---

## License

This project is intended for academic and research purposes.
