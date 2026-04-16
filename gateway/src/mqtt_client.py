import paho.mqtt.client as mqtt

BROKER = 'broker.hivemq.com'
PORT = 1883

TOPIC_LIGHT = "bk-iot-light"
TOPIC_TEMP = "bk-iot-temp"
TOPIC_HUMI = "bk-iot-humi"
TOPIC_LED = "bk-iot-led"
TOPIC_FAN = "bk-iot-fan"
TOPIC_IR = "bk-iot-ir"

class MQTT_Control:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def set_uart(self, uart_control):
        self.uart = uart_control

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT Broker...")

        client.subscribe(TOPIC_LED)
        client.subscribe(TOPIC_FAN)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        if topic == TOPIC_LED:
            self.uart.send_command(f"!1:LED:{payload}#")
        elif topic == TOPIC_FAN:
            self.uart.send_command(f"!1:FAN:{payload}#")

        print(f"Recivied {payload} from {topic}")

    def connect(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def publish(self, topic, value):
        self.client.publish(topic, value)