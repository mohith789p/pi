# Import libraries
import cv2
import mediapipe as mp
import time
from pynput.keyboard import Key, Controller

# Initialize Keyboard Controller
keyboard = Controller()

# Initialize MediaPipe Hands module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Function to map gestures to YouTube keyboard actions
def execute_keyboard_control(gesture):
    try:
        if gesture == "PLAY_PAUSE":
            keyboard.press('k')
            keyboard.release('k')
            return "PAUSE/PLAY (K)"
        elif gesture == "VOL_UP":
            keyboard.press(Key.up)
            keyboard.release(Key.up)
            return "VOLUME UP"
        elif gesture == "VOL_DOWN":
            keyboard.press(Key.down)
            keyboard.release(Key.down)
            return "VOLUME DOWN"
        elif gesture == "MUTE":
            keyboard.press('m')
            keyboard.release('m')
            return "MUTE (M)"
    except Exception as e:
        print(f"[WARNING] Keyboard access failed: {e}")
    return ""

# Setup camera capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot access camera. Make sure /dev/video0 is exposed to Docker.")

# Initialize timing variables
last_action_time = 0
debounce_delay = 1.2
feedback_msg = "System Ready"
current_gesture = "None"

# Inform user system has started
print("System Started. Focus your YouTube tab now.")

# Main loop to capture frames and detect gestures
while cap.isOpened():
    success, img = cap.read()
    if not success:
        print("[ERROR] Failed to read from camera.")
        break

    # Mirror image for natural interaction
    img = cv2.flip(img, 1)

    # Convert to RGB for MediaPipe processing
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Process image to detect hands
    results = hands.process(img_rgb)
    active_gesture = None

    # Check for hand landmarks
    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            lm = hand_lms.landmark

            # Detect open palm for play/pause
            is_open = lm[8].y < lm[6].y and lm[12].y < lm[10].y and \
                      lm[16].y < lm[14].y and lm[20].y < lm[18].y

            # Detect thumb up for volume up
            is_thumb_up = lm[4].y < lm[2].y and lm[8].y > lm[6].y

            # Detect thumb down for volume down
            is_thumb_down = lm[4].y > lm[5].y and lm[8].y > lm[6].y

            # Detect fist for mute
            is_fist = lm[8].y > lm[6].y and lm[12].y > lm[10].y and \
                      lm[16].y > lm[14].y and lm[20].y > lm[18].y

            # Execute action if debounce delay passed
            if time.time() - last_action_time > debounce_delay:
                if is_open:
                    active_gesture = "PLAY_PAUSE"
                elif is_thumb_up:
                    active_gesture = "VOL_UP"
                elif is_thumb_down:
                    active_gesture = "VOL_DOWN"
                elif is_fist:
                    active_gesture = "MUTE"

                if active_gesture:
                    feedback_msg = execute_keyboard_control(active_gesture)
                    current_gesture = active_gesture
                    last_action_time = time.time()

            # Draw hand landmarks on frame
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

    # Draw HUD background
    cv2.rectangle(img, (0, 0), (320, 90), (0, 0, 0), -1)

    # Display current gesture
    cv2.putText(img, f"GESTURE: {current_gesture}", (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Display last executed action
    cv2.putText(img, f"ACTION: {feedback_msg}", (15, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # Show frame in window
    cv2.imshow("Touchless YouTube Control", img)

    # Exit loop if 'q' pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting...")
        break

# Release camera and destroy windows
cap.release()
cv2.destroyAllWindows()
hands.close()
