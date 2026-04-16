import time
import os
import cv2  # Thêm thư viện OpenCV
from uart import UART_Control
from mqtt_client import MQTT_Control, TOPIC_LIGHT, TOPIC_TEMP, TOPIC_HUMI, TOPIC_IR
import ctypes
import joblib
import numpy as np
import keyboard  

def bring_window_to_front(window_name):
    """Ép cửa sổ OpenCV hiện lên trên cùng (Windows only)"""
    hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
    if hwnd:
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9

# Cấu hình đường dẫn dữ liệu
ROUTES = {
    "LIGHT": TOPIC_LIGHT,
    "TEMP": TOPIC_TEMP,
    "HUMI": TOPIC_HUMI,
    "IR": TOPIC_IR
}

try:
    model_occupancy = joblib.load('occupancy_model.pkl')
    model_comfort = joblib.load('comfort_model.pkl')
    print("--- Đã nạp thành công các mô hình AI ---")
except:
    print("--- Chưa có file model. Chạy chế độ mô phỏng... ---")
    model_occupancy = None

# 1. Khởi tạo kết nối UART và MQTT
uart = UART_Control()
uart.connect()

mqtt = MQTT_Control()
mqtt.set_uart(uart)
mqtt.connect()

# 2. Khởi tạo Camera Laptop (Cổng 0 thường là camera mặc định)
cap = cv2.VideoCapture(0)
cam_enabled = True # Biến trạng thái để bật/tắt hiển thị Cam

print("--- Hệ thống đang chạy ---")
print("- Nhấn 'c' để BẬT/TẮT cửa sổ Camera")
print("- Nhấn 's' để giả lập AI (kể cả khi tắt Cam cửa sổ)")
print("- Nhấn 'q' để thoát hoàn toàn")



led_state = False
window_name = "Smart Home AI Gateway"
window_open = False
temp_val = 25.0
humid_val = 50.0
light_val = 1000.0

while True:
    ret, frame = cap.read()

    # HIỂN THỊ CAMERA
    if ret and cam_enabled:
        if not window_open:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 640, 480)
            window_open = True
        cv2.imshow(window_name, frame)

    if cam_enabled:
        cv2.waitKey(1)

    if keyboard.is_pressed('c'):
        cam_enabled = not cam_enabled
        print(f"Trạng thái Camera: {'HIỆN' if cam_enabled else 'ẨN'}")

        if not cam_enabled:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            window_open = False

        time.sleep(0.3)  

    elif keyboard.is_pressed('s'):
        led_state = not led_state
        if led_state:
            print("[AI EVENT] Bật đèn!")
            uart.send_command("!1:LED:1#")
            mqtt.publish("bk-iot-led", "1")
        else:
            print("[AI EVENT] Tắt đèn!")
            uart.send_command("!1:LED:0#")
            mqtt.publish("bk-iot-led", "0")
        time.sleep(0.3)  # debounce

    elif keyboard.is_pressed('q'):
        print("Đang tắt hệ thống...")
        uart.send_command("!1:LED:0#")
        time.sleep(0.1)
        uart.send_command("!1:FAN:0#")
        break

    if model_occupancy:
            # Input: [Temperature, Humidity, Light, CO2, HumidityRatio]
            # CO2 và HumidityRatio tạm thời để giá trị trung bình từ Dataset
            input_data = np.array([[temp_val, humid_val, light_val, 400, 0.001]]) 
            
            is_occupied = model_occupancy.predict(input_data)[0]
            if is_occupied == 1:
                print("AI: Phát hiện có người! Tự động giữ đèn SÁNG.")
                uart.send_command("!1:LED:1#")
                mqtt.publish(TOPIC_LED, "1")
            else:
                print("AI: Không có người. Tắt đèn.")
                uart.send_command("!1:LED:0#")
                mqtt.publish(TOPIC_LED, "0")

    # ĐỌC UART
    raw_data = uart.read_data()
    if raw_data and raw_data.startswith("!") and raw_data.endswith("#"):
            parts = raw_data[1:-1].split(":")
            if len(parts) == 3:
                _, data_type, value = parts
                if data_type == "TEMP": temp_val = float(value)
                if data_type == "HUMI": humid_val = float(value)
                if data_type == "LIGHT": light_val = float(value)

                topic = ROUTES.get(data_type)
                if topic:
                    mqtt.publish(topic, value)
                    print(f"[UART] Nhận {data_type}: {value} -> Published")

    time.sleep(0.01)

cap.release()
cv2.destroyAllWindows()