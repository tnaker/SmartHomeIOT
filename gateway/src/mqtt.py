from Adafruit_IO import MQTTClient

class MQTT_Control:
    def __init__(self, user, key):
        self.client = MQTTClient(user, key)
        self.client.on_connect = self.on_connected
        self.client.on_message = self.on_message
        self.on_msg_callback = None # Sẽ gán hàm xử lý từ main.py

    def on_connected(self, client):
        print("--- Đã kết nối thành công với Adafruit Cloud ---")
        # Đăng ký nhận dữ liệu từ các nút nhấn
        client.subscribe("bk-iot-led")
        client.subscribe("bk-iot-fan")

    def on_message(self, client, feed_id, payload):
        print(f"Nhận lệnh từ Cloud: [{feed_id}] = {payload}")
        if self.on_msg_callback:
            self.on_msg_callback(feed_id, payload)

    def connect(self):
        self.client.connect()
        self.client.loop_background()

    def publish(self, feed_id, value):
        self.client.publish(feed_id, value)