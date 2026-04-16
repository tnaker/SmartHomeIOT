import time
import os
import cv2  # Thêm thư viện OpenCV
from uart import UART_Control
from mqtt_client import MQTT_Control, TOPIC_LIGHT, TOPIC_TEMP, TOPIC_HUMI, TOPIC_IR

import ctypes

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

import keyboard  # Thêm vào đầu file

led_state = False
window_name = "Smart Home AI Gateway"
window_open = False

while True:
    ret, frame = cap.read()

    # HIỂN THỊ CAMERA
    if ret and cam_enabled:
        if not window_open:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 640, 480)
            window_open = True
        cv2.imshow(window_name, frame)

    # ✅ waitKey chỉ cần để OpenCV xử lý GUI, không dùng để bắt phím nữa
    if cam_enabled:
        cv2.waitKey(1)

    # ✅ Bắt phím bằng keyboard — hoạt động dù cửa sổ OpenCV có mở hay không
    if keyboard.is_pressed('c'):
        cam_enabled = not cam_enabled
        print(f"Trạng thái Camera: {'HIỆN' if cam_enabled else 'ẨN'}")

        if not cam_enabled:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            window_open = False

        time.sleep(0.3)  # ✅ Chống nhấn lặp (debounce)

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

    # ĐỌC UART
    raw_data = uart.read_data()
    if raw_data:
        if raw_data.startswith("!") and raw_data.endswith("#"):
            parts = raw_data[1:-1].split(":")
            if len(parts) == 3:
                device_id, data_type, value = parts
                topic = ROUTES.get(data_type)
                if topic:
                    mqtt.publish(topic, value)
                    print(f"[UART] Nhận {data_type}: {value} -> Published")
                else:
                    print(f"[UART] Unknown data type: {data_type}")

    time.sleep(0.01)

cap.release()
cv2.destroyAllWindows()