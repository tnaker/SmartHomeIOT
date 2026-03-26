import serial.tools.list_ports

class UART_Control:
    def __init__(self):
        self.ser = None
        self.port = self.find_port()

    def find_port(self):
        # Tự động tìm cổng có mô tả là USB hoặc UART
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB" in port.description or "UART" in port.description:
                return port.device
        return None

    def connect(self):
        if self.port:
            try:
                self.ser = serial.Serial(port=self.port, baudrate=115200, timeout=1)
                print(f"--- Đã kết nối với cổng: {self.port} ---")
            except Exception as e:
                print(f"Lỗi kết nối Serial: {e}")
        else:
            print("--- Không tìm thấy bộ Kit Yolo:Bit! ---")

    def read_data(self):
        try:
            if self.ser and self.ser.inWaiting() > 0:
                return self.ser.readline().decode('utf-8').strip()
        except:
            print("Mất kết nối với bộ Kit... Đang thử kết nối lại...")
            self.connect() # Tự động tìm lại cổng COM
        return ""
    def send_command(self, cmd):
        if self.ser:
            self.ser.write(str(cmd).encode())