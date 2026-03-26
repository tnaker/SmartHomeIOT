import time
from yolobit import *
from button import *
import machine
from homebit3_lcd1602 import LCD1602
from homebit3_dht20 import DHT20
from aiot_rgbled import RGBLed


"""
P3/P6: Quạt mini
P14/P15: module 4 led
I2C2: Cảm biết nhiệt độ, độ ẩm DHT20
I2C1: LCD
P0: cảm biến ánh sáng
"""

# Khai báo dải đèn LED (Neopixel/RGB) trên P14 với tên gọi tiny_rgb
tiny_rgb = RGBLed(pin14.pin, 4)

# Khởi tạo các đối tượng từ thư viện HomeBit v3
lcd = LCD1602()
dht = DHT20()

# Hàm hỗ trợ chuyển đổi mã màu HEX sang RGB tuple
# Thường được dùng cho các hàm yêu cầu argument là (R, G, B)
def hex_to_rgb(hex_str):
  # Xử lý chuỗi (loại bỏ dấu # nếu có)
  hex_str = hex_str.lstrip('#')
  return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# Bật đèn nền LCD trước khi chạy
lcd.backlight_on()
lcd.clear()

while True:
  # Gọi hàm đọc cảm biến
  light_val = pin0.read_analog()
  dht.read_dht20()
  temp_val = dht.dht20_temperature()
  humi_val = dht.dht20_humidity()
  
  # Hiển thị thông số lên màn hình LCD dòng 0
  lcd.move_to(0, 0)
  lcd.putstr('T:')
  lcd.putstr(str(temp_val))
  lcd.putstr('C L:')
  lcd.putstr(str(light_val))
  
  # Hiển thị độ ẩm dòng 1
  lcd.move_to(0, 1)
  lcd.putstr('H:')
  lcd.putstr(str(humi_val))
  lcd.putstr('%')

  # Khối Lệnh Nếu - Cảm biến ánh sáng mở Quạt Mini (P3)
  # Lưu ý: Theo khối lệnh trong JSON, điều kiện đang được tạm khóa là False
  if False: #light_val > 4000:
    pin3.write_analog(1020)
  else:
    pin3.write_analog(0)

  # Khối Lệnh Nếu - Cảm biến nhiệt độ điều khiển 4 Đèn LED (P14)
  # Nếu nhiệt độ > 32 độ C thì bật 4 LED màu đỏ
  if humi_val > 50:
    for i in range(4):
      # Cấu trúc: tiny_rgb.show(vị trí, (r, g, b))
      tiny_rgb.show(i, hex_to_rgb("#FF0000"))
  else:
    for i in range(4):
      tiny_rgb.show(i, hex_to_rgb("#000000"))

  # Khối Lệnh Dừng (Chờ)
  time.sleep_ms(1000)
