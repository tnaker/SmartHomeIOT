import time
import os
from uart import UART_Control
from mqtt_client import MQTT_Control, TOPIC_LIGHT, TOPIC_TEMP, TOPIC_HUMI, TOPIC_IR

ROUTES = {
    "LIGHT": TOPIC_LIGHT,
    "TEMP": TOPIC_TEMP,
    "HUMI": TOPIC_HUMI,
    "IR": TOPIC_IR
}

uart = UART_Control()
uart.connect()

mqtt = MQTT_Control()
mqtt.set_uart(uart)
mqtt.connect()

while True:
    raw_data = uart.read_data()
    if not raw_data:
        time.sleep(0.1)
        continue
    if raw_data.startswith("!") and raw_data.endswith("#"):
        parts = raw_data[1:-1].split(":")
        if len(parts) == 3:
            device_id, data_type, value = parts
            topic = ROUTES.get(data_type)
            if not topic:
                print(f"Unknown data type: {data_type}")
                time.sleep(0.1)
                continue
            mqtt.publish(topic, value)
    
    # 2. KHU VỰC DÀNH CHO AI (Báo cáo cuối kỳ)
    # Tại đây, bạn sẽ mở Camera và gọi model AI
    # if AI_DETECT_PERSON: uart.send_command("!1:LED:1#")
    
    time.sleep(0.1)