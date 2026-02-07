import cv2
import mediapipe as mp
import time
from pynput.keyboard import Key, Controller

# Initialize Keyboard Controller
keyboard = Controller()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=1, 
    min_detection_confidence=0.8,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

def execute_keyboard_control(gesture):
    """
    Simulates YouTube-specific keyboard shortcuts.
    'k' = Play/Pause (More reliable than Space)
    'up/down' = YouTube internal volume
    'm' = Mute
    """
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
    
    return ""

# Camera Setup
cap = cv2.VideoCapture(0)
last_action_time = 0
debounce_delay = 1.2  # Seconds to wait between actions
feedback_msg = "System Ready"
current_gesture = "None"

print("System Started. Focus your YouTube tab now.")

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break
    
    # Mirror the image for intuitive interaction
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    active_gesture = None

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            lm = hand_lms.landmark
            
            # --- GESTURE DETECTION LOGIC ---
            
            # 1. Open Palm (Play/Pause)
            # Logic: All 4 fingers are extended (y-coordinate of tip < y-coordinate of joint)
            is_open = (lm[8].y < lm[6].y and lm[12].y < lm[10].y and 
                       lm[16].y < lm[14].y and lm[20].y < lm[18].y)
            
            # 2. Thumb Up (Volume Up)
            # Logic: Thumb is high, Index is closed
            is_thumb_up = lm[4].y < lm[2].y and lm[8].y > lm[6].y
            
            # 3. Thumb Down (Volume Down)
            # Logic: Thumb is low, Index is closed
            is_thumb_down = lm[4].y > lm[5].y and lm[8].y > lm[6].y

            # 4. Fist (Mute)
            # Logic: All fingers closed (tips below joints)
            is_fist = (lm[8].y > lm[6].y and lm[12].y > lm[10].y and 
                       lm[16].y > lm[14].y and lm[20].y > lm[18].y)

            # --- EXECUTION ---
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

            # Draw landmarks on the frame
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

    # --- VISUAL HUD OVERLAY ---
    # Black bar for readability
    cv2.rectangle(img, (0, 0), (320, 90), (0, 0, 0), -1)
    cv2.putText(img, f"GESTURE: {current_gesture}", (15, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(img, f"ACTION: {feedback_msg}", (15, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow("Touchless YouTube Control", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
