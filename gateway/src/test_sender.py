import time
import os
from mqtt import MQTT_Control
from dotenv import load_dotenv

load_dotenv()

AIO_USER = os.getenv("ADAFRUIT_IO_USERNAME")
AIO_KEY = os.getenv("ADAFRUIT_IO_KEY")

client = MQTT_Control(AIO_USER, AIO_KEY)
client.connect()

time.sleep(1)

while True:
    import random
    fake_temp = random.randint(25, 30)
    fake_light = random.randint(1000, 4000)
    print(f"Đang gửi nhiệt độ giả: {fake_light}")
    client.publish("bk-iot-light", fake_light)
    print(f"Đang gửi nhiệt độ giả: {fake_temp}")
    client.publish("bk-iot-temp", fake_temp)
    time.sleep(5)