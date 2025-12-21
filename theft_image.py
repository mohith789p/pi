import cv2
import numpy as np
from ultralytics import YOLO

MODEL_PATH = "../models/yolov8n.pt"
IMAGE_PATH = "../OIP.webp"

PIXEL_DISTANCE = 120
THEFT_HENS = 2

model = YOLO(MODEL_PATH)
img = cv2.imread(IMAGE_PATH)

results = model(img, verbose=False)

humans, hens = [], []

if results and hasattr(results[0], "boxes"):
    for box in results[0].boxes:
        cls = int(box.cls)
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if cls == 0:      # person
            humans.append((cx, cy))
        elif cls == 1:    # hen
            hens.append((cx, cy))

suspicious = False
for hx, hy in humans:
    nearby = sum(
        1 for (x, y) in hens
        if np.linalg.norm([hx - x, hy - y]) < PIXEL_DISTANCE
    )
    if nearby >= THEFT_HENS:
        suspicious = True
        break

if suspicious:
    print("⚠️ POTENTIAL RISK DETECTED (Image-based)")
else:
    print("✅ No suspicious activity detected")

cv2.imshow("Image Check", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
