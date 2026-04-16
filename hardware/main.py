import time
from yolobit import *
from button import *
import machine
from homebit3_lcd1602 import LCD1602
from homebit3_dht20 import DHT20
from aiot_rgbled import RGBLed
from aiot_ir_receiver import IR_RX

"""
Cấu hình chân Yolo:bit:
- P0:       Module 4 LED (RGBLed)
- P2:       Cảm biến ánh sáng (analog)
- I2C1:     LCD 1602
- P10/P13:  Quạt mini (PWM)
- P3/P6:    Cảm biến hồng ngoại (IR Receiver)
- I2C2:     Cảm biến nhiệt độ, độ ẩm DHT20

Giao tiếp: UART qua USB với Gateway (protocol: !ID:TYPE:VALUE#)
"""

# ===== KHỞI TẠO PHẦN CỨNG =====
tiny_rgb = RGBLed(pin0.pin, 4)   # P0: 4 LED
lcd = LCD1602()                   # I2C1: LCD
try:
    from yolobit import i2c as global_i2c
except:
    global_i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21))

dht = DHT20(global_i2c)           # I2C2: Cảm biến nhiệt độ, độ ẩm

# P10/P13: Quạt mini (dùng pin10 để điều khiển PWM)
# P3/P6:   Cảm biến hồng ngoại

# Trạng thái hiện tại
led_state = 0
fan_state = 0

# ===== HÀM HỖ TRỢ =====
def hex_to_rgb(hex_str):
    """Chuyển đổi mã HEX sang RGB tuple"""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def set_led(state):
    """Bật/tắt 4 LED"""
    global led_state
    led_state = state
    color = "#FFFFFF" if state else "#000000"
    for i in range(4):
        tiny_rgb.show(i, hex_to_rgb(color))

def set_fan(state):
    """Bật/tắt quạt mini qua P10"""
    global fan_state
    fan_state = state
    if state:
        pin10.write_analog(1020)
    else:
        pin10.write_analog(0)

def send_uart(data_type, value):
    """Gửi dữ liệu qua UART theo protocol: !ID:TYPE:VALUE#"""
    msg = "!1:{}:{}#".format(data_type, value)
    print(msg)

# ===== CALLBACK: Xử lý lệnh hồng ngoại =====
ir_code_received = None

def on_ir_receive(data, addr, ctrl):
    """Callback khi nhận tín hiệu hồng ngoại"""
    global ir_code_received
    ir_code_received = data
    print("IR code:", data)

# Khởi tạo IR Receiver trên P3
try:
    ir_pin = machine.Pin(pin3.pin, machine.Pin.IN)
    ir_rx = IR_RX(ir_pin, on_ir_receive)
    print("IR Receiver initialized on P3")
except:
    ir_rx = None
    print("IR Receiver not available")

# ===== KHỞI TẠO LCD =====
lcd.backlight_on()
lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("Smart Home IoT")
lcd.move_to(0, 1)
lcd.putstr("Starting...")
time.sleep(2)

lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("READY!")
print("--- Kit da san sang ---")
time.sleep(1)

# ===== BUFFER ĐỌC LỆNH TỪ GATEWAY =====
import sys
import select

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

uart_buffer = ""

def check_uart_commands():
    """Đọc và xử lý lệnh từ Gateway qua UART (stdin/print)"""
    global uart_buffer, led_state, fan_state
    try:
        # Kiểm tra xem có dữ liệu trong stdin không (non-blocking)
        if poll.poll(0):
            data = sys.stdin.read(1)
            if data:
                uart_buffer += data
                # Kiểm tra xem có lệnh hoàn chỉnh chưa
                while "!" in uart_buffer and "#" in uart_buffer:
                    start = uart_buffer.index("!")
                    end = uart_buffer.index("#")
                    if start < end:
                        cmd = uart_buffer[start+1:end]
                        uart_buffer = uart_buffer[end+1:]
                        process_command(cmd)
                    else:
                        uart_buffer = uart_buffer[start:]
                        break
    except:
        pass

def process_command(cmd):
    """Xử lý lệnh nhận được: ID:TYPE:VALUE"""
    print("[DEBUG] Yolo:Bit processing command:", cmd)
    global led_state, fan_state
    parts = cmd.split(":")
    if len(parts) == 3:
        device_id, data_type, value = parts
        if data_type == "LED":
            if value == "1":
                set_led(1)
                print("LED -> ON")
            else:
                set_led(0)
                print("LED -> OFF")
        elif data_type == "FAN":
            if value == "1":
                set_fan(1)
                print("FAN -> ON")
            else:
                set_fan(0)
                print("FAN -> OFF")

# ===== VÒNG LẶP CHÍNH =====
SEND_INTERVAL = 10  # Gửi dữ liệu mỗi 10 giây
last_send_time = time.ticks_ms()

while True:
    # 1. Kiểm tra lệnh điều khiển từ Gateway (non-blocking)
    check_uart_commands()

    # 2. Kiểm tra tín hiệu hồng ngoại
    if ir_code_received is not None:
        print("[DEBUG] Gửi IR lên Server:", ir_code_received)
        # Gửi mã IR lên server
        send_uart("IR", str(ir_code_received))
        ir_code_received = None

    # 3. ĐỌC CẢM BIẾN (theo chu kỳ)
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_send_time) >= SEND_INTERVAL * 1000:
        last_send_time = current_time
        print("[DEBUG] --- Đọc chu kỳ cảm biến ---")

        try:
            # Đọc cảm biến ánh sáng (P2)
            light_val = pin2.read_analog()
            
            # Đọc cảm biến nhiệt độ / độ ẩm (I2C2)
            dht.read_dht20()
            temp_val = dht.dht20_temperature()
            humi_val = dht.dht20_humidity()
            print("[DEBUG] Sensors -> T:{} H:{} L:{}".format(temp_val, humi_val, light_val))
        except Exception as e:
            print("[DEBUG] LỖI đọc cảm biến:", e)
            continue

        # Hiển thị lên LCD
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr('T:')
        lcd.putstr(str(temp_val))
        lcd.putstr('C L:')
        lcd.putstr(str(light_val))

        lcd.move_to(0, 1)
        lcd.putstr('H:')
        lcd.putstr(str(humi_val))
        lcd.putstr('% ')
        lcd.putstr('F:' if fan_state else 'f:')
        lcd.putstr('L:' if led_state else 'l:')

        # Gửi dữ liệu cảm biến lên Gateway qua UART
        send_uart("LIGHT", str(light_val))
        send_uart("TEMP", str(temp_val))
        send_uart("HUMI", str(humi_val))

    # Nghỉ ngắn để tránh quá tải CPU
    time.sleep_ms(100)
