import cv2
import requests
import time
from ultralytics import YOLO
from twilio.rest import Client

# --- ESP32 Configuration ---
ESP32_IP = "**.***.**.***"  # For sending count to esp32 module
ESP32_PORT = 80
ENDPOINT = "/update-count"
API_URL = f"http://{ESP32_IP}:{ESP32_PORT}{ENDPOINT}"

# --- ESP32-CAM Stream Source ---
STREAM_URL = "http://10.106.80.43:81/stream"  # ✅ Correct MJPEG stream URL ex-ip-address=10.106.80.43

# --- YOLOv8 Setup ---
MODEL_PATH = 'yolov8n.pt'
model = YOLO(MODEL_PATH)
PERSON_CLASS_ID = 0
CONFIDENCE_THRESHOLD = 0.5 #vary this as per accuracy needs

# --- Video Source ---
cap = cv2.VideoCapture(STREAM_URL)
time.sleep(2)  # Give stream time to initialize
if not cap.isOpened():
    print(f"❌ Error: Could not open ESP32 stream at {STREAM_URL}")
    exit()

# --- Throttle Settings ---
SEND_INTERVAL_SECONDS = 1.0
last_send_time = time.time()

# --- Crowd Threshold for SMS Alert ---
CROWD_SMS_THRESHOLD = 5
last_sms_time = 0
SMS_INTERVAL_SECONDS = 60

# --- Twilio SMS Setup --- // set your own twilio acc and get ur credentials and paste it below
TWILIO_SID = "---------------------"
TWILIO_AUTH_TOKEN = "-------------"
TWILIO_PHONE = "+************"
TARGET_PHONE = "+91********"

twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def send_sms_alert(count):
    global last_sms_time
    now = time.time()
    if now - last_sms_time < SMS_INTERVAL_SECONDS:
        return

    message = f"⚠️ Crowd Alert: {count} people detected!"
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=TARGET_PHONE
        )
        print(f"[{time.strftime('%H:%M:%S')}] 📱 SMS sent: {message}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ SMS failed: {e}")
    finally:
        last_sms_time = now

def send_count_to_esp32(count):
    global last_send_time
    current_time = time.time()
    if current_time - last_send_time < SEND_INTERVAL_SECONDS:
        return

    try:
        payload = str(count)
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(API_URL, data=payload, headers=headers, timeout=0.5)
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] Count Sent: {count}. Status: OK.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ESP32 returned status code {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"[{time.strftime('%H:%M:%S')}] Timeout connecting to ESP32.")
    except requests.exceptions.ConnectionError:
        print(f"[{time.strftime('%H:%M:%S')}] Connection error to ESP32.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Unexpected error: {e}")

    last_send_time = current_time

print(f"--- Crowd Detection Running. Input Stream: {STREAM_URL} ---")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Error reading frame from ESP32 stream.")
        break

    results = model(frame, classes=[PERSON_CLASS_ID], conf=CONFIDENCE_THRESHOLD, verbose=False)
    crowd_count = len(results[0].boxes) if results and results[0].boxes else 0

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f'Crowd Count: {crowd_count}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow('YOLOv8 Crowd Detector (ESP32 Stream)', annotated_frame)

    send_count_to_esp32(crowd_count)

    if crowd_count > CROWD_SMS_THRESHOLD:
        print(f"[{time.strftime('%H:%M:%S')}] 🚨 Crowd count {crowd_count} exceeds threshold {CROWD_SMS_THRESHOLD}")
        send_sms_alert(crowd_count)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
