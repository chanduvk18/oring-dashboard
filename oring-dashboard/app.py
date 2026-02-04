import cv2
import requests
import threading
import time
import queue
from ultralytics import YOLO

# ==========================================
# 🛑 CONFIGURATION
# ==========================================
THINGSPEAK_KEY = "YPMA6U83XI6O56DM"
TELEGRAM_TOKEN = "7953532460:AAHH-4rV2Zi9Pi3DA1Dy8AUGaGW6Fwje3mM"
CHAT_ID = "1912477648"
CAMERA_URL = "http://10.151.30.206:8080/video"
MODEL_FILE = "best.pt"
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbzNtMghS_xCZcZvJpEfYBLZnnjQwgzQNH48Wo52vRYkFOmD1T3k6unH4Bk2k8BmT_64FQ/exec"

# --- GLOBAL COUNTERS ---
cnt_total = 0
cnt_flash = 0
cnt_crack = 0
cnt_break = 0

# ==========================================
# 🧵 THREADED VIDEO STREAM CLASS (THE LAG FIX)
# ==========================================
class VideoStream:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        # We only keep the 1 newest frame in the queue to ensure zero lag
        self.q = queue.Queue(maxsize=1) 
        self.stopped = False
        
    def start(self):
        # Starts a background thread to keep reading frames
        threading.Thread(target=self.update, daemon=True).start()
        return self
        
    def update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                return
            
            # If a new frame comes in, throw away the old one
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()

# ==========================================
# ☁️ IOT FUNCTIONS
# ==========================================
def send_smart_alert(defect_type):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    msg = f"🚨 Alert: {defect_type} detected!"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=2)
    except: 
        pass

def update_cloud_database(defect_type, confidence):
    """Sends a single row of data to Google Sheets via Web App"""
    params = {
        "defect": defect_type,
        "conf": f"{confidence:.2f}"
    }
    try:
        # We use a simple GET request which is very fast
        requests.get(GOOGLE_URL, params=params, timeout=3)
    except:
        pass

# In your Main Loop, call it like this:
# threading.Thread(target=update_cloud_database, args=(current_defect, conf)).start()

# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================
print("------------------------------------------------")
print("🚀 Starting Optimized O-Ring Inspection...")
print("------------------------------------------------")

try:
    model = YOLO(MODEL_FILE)
    # Start the background camera thread
    vs = VideoStream(CAMERA_URL).start()
    time.sleep(2.0) # Wait for camera to stabilize
except Exception as e:
    print(f"❌ Initialization Error: {e}")
    exit()

prev_time = 0
print("👉 Press 'q' to quit.")

while True:
    # Get the freshest frame from the worker thread
    frame = vs.read()
    
    # Calculate FPS
    new_time = time.time()
    fps = 1 / (new_time - prev_time)
    prev_time = new_time

    # Run YOLO Detection
    results = model(frame, conf=0.45, verbose=False, stream=True)
    
    current_defect = None
    # Draw results
    for r in results:
        frame = r.plot() 
        for box in r.boxes:
            cls = int(box.cls[0])
            name = model.names[cls]
            if name == '1': current_defect = "FLASHES"
            elif name == '2': current_defect = "CRACK"
            elif name == '3': current_defect = "BREAKAGE"

    # Trigger IoT alerts if a defect is found
    if current_defect:
        cnt_total += 1
        if current_defect == "FLASHES": cnt_flash += 1
        elif current_defect == "CRACK": cnt_crack += 1
        elif current_defect == "BREAKAGE": cnt_break += 1
        
        print(f"⚠️ {current_defect} Detected! Logging...")
        threading.Thread(target=send_smart_alert, args=(current_defect,)).start()
        threading.Thread(target=update_all_graphs).start()

    # Overlay FPS on the screen
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.imshow("O-Ring Inspection (Zero-Lag)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        vs.stopped = True
        break

cv2.destroyAllWindows()