import time
import os
from uart import UART_Control
from mqtt import MQTT_Control
from dotenv import load_dotenv

load_dotenv() # Tải các biến từ file .env

AIO_USER = os.getenv("ADAFRUIT_IO_USERNAME")
AIO_KEY = os.getenv("ADAFRUIT_IO_KEY")

# Khởi tạo các module
uart = UART_Control()
mqtt = MQTT_Control(AIO_USER, AIO_KEY)

# Hàm xử lý khi có lệnh từ Web (Chiều xuống)
def handle_command_from_web(feed_id, payload):
    # Chuyển đổi payload (0/1) thành giao thức Kit hiểu
    if feed_id == "bk-iot-led":
        uart.send_command(f"!1:LED:{payload}#")
    elif feed_id == "bk-iot-fan":
        uart.send_command(f"!1:FAN:{payload}#")

# Gán callback và kết nối
mqtt.on_msg_callback = handle_command_from_web
uart.connect()
mqtt.connect()

print("--- Hệ thống Gateway đang chạy... ---")

while True:
    # 1. CHIỀU LÊN: Kit -> Máy tính -> Cloud
    raw_data = uart.read_data()
    if raw_data.startswith("!") and raw_data.endswith("#"):
        # Phân tích chuỗi !1:TEMP:28#
        parts = raw_data[1:-1].split(":")
        if len(parts) == 3:
            device_id, data_type, value = parts
            if data_type == "TEMP":
                mqtt.publish("bk-iot-temp", value)
            elif data_type == "LIGHT":
                mqtt.publish("bk-iot-light", value)
    
    # 2. KHU VỰC DÀNH CHO AI (Báo cáo cuối kỳ)
    # Tại đây, bạn sẽ mở Camera và gọi model AI
    # if AI_DETECT_PERSON: uart.send_command("!1:LED:1#")
    
    time.sleep(0.1) # Tránh quá tải CPU