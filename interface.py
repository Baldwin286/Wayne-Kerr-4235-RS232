import sys
import serial
import serial.tools.list_ports  # Thư viện để quét cổng COM
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QPushButton, QTextEdit, QComboBox, QLabel, QHBoxLayout)

class LCRControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.initUI()
        self.refresh_ports() # Tự động quét cổng khi mở ứng dụng

    def initUI(self):
        self.setWindowTitle('Wayne Kerr 4300 RS232 Control')
        layout = QVBoxLayout()

        # Cấu hình kết nối với QComboBox
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel('Cổng COM:'))
        
        self.combo_ports = QComboBox()
        config_layout.addWidget(self.combo_ports, 1) # Cho phép ComboBox dãn ra
        
        self.btn_refresh = QPushButton('Quét lại')
        self.btn_refresh.clicked.connect(self.refresh_ports)
        config_layout.addWidget(self.btn_refresh)
        
        self.btn_connect = QPushButton('Kết nối')
        self.btn_connect.clicked.connect(self.toggle_connection)
        config_layout.addWidget(self.btn_connect)
        layout.addLayout(config_layout)

        # Các nút điều khiển máy LCR 4300 [cite: 1893]
        controls = [
            ('Đo (Trigger)', ':MEAS:TRIG?'),
            ('Đặt tần số 1kHz', ':MEAS:FREQ 1000'),
            ('Reset máy (*RST)', '*RST'),
            ('Kiểm tra định danh (*IDN?)', '*IDN?')
        ]

        for text, cmd in controls:
            btn = QPushButton(text)
            btn.clicked.connect(lambda ch, c=cmd: self.send_command(c))
            layout.addWidget(btn)

        # Khu vực log hiển thị phản hồi
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(QLabel('Phản hồi từ máy:'))
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def refresh_ports(self):
        """Quét danh sách các cổng COM đang hoạt động trên PC"""
        self.combo_ports.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.combo_ports.addItem(port.device) # port.device là tên như COM1, COM2...
        
        if self.combo_ports.count() == 0:
            self.log_output.append("Không tìm thấy cổng COM nào.")

    def toggle_connection(self):
        if self.ser is None or not self.ser.is_open:
            current_port = self.combo_ports.currentText()
            if not current_port:
                self.log_output.append("Vui lòng chọn một cổng COM.")
                return
                
            try:
                # Cấu hình Protocol theo datasheet: 9600, 8, N, 1 [cite: 1821, 1823, 1825, 1827]
                self.ser = serial.Serial(
                    port=current_port,
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1
                )
                self.log_output.append(f"--- Đã kết nối với {current_port} ---")
                self.btn_connect.setText("Ngắt kết nối")
                self.combo_ports.setEnabled(False) # Khóa combo box khi đang kết nối
            except Exception as e:
                self.log_output.append(f"Lỗi kết nối: {str(e)}")
        else:
            self.ser.close()
            self.ser = None
            self.btn_connect.setText("Kết nối")
            self.combo_ports.setEnabled(True)
            self.log_output.append("--- Đã ngắt kết nối ---")

    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                # Luôn kết thúc bằng \n (LF) cho RS232 [cite: 1832]
                self.ser.write(f"{cmd}\n".encode('ascii'))
                self.log_output.append(f"Gửi: {cmd}")
                
                if "?" in cmd:
                    response = self.ser.readline().decode('ascii').strip()
                    self.log_output.append(f"Nhận: {response}")
            except Exception as e:
                self.log_output.append(f"Lỗi: {str(e)}")
        else:
            self.log_output.append("Chưa kết nối máy đo!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRControlApp()
    ex.show()
    sys.exit(app.exec_())