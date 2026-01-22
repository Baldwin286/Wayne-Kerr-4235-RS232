import sys
import serial
import serial.tools.list_ports
import time
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog)

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.current_row = 0
        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('Wayne Kerr 4300 - Đo Batch 125 LK (Lx Qx Ly Qy Lz Qz Rx Ry Rz)')
        self.resize(1200, 700)
        layout = QVBoxLayout()

        # 1. Kết nối
        conn_layout = QHBoxLayout()
        self.combo_ports = QComboBox()
        self.btn_connect = QPushButton('Kết nối')
        self.btn_connect.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(QLabel('Cổng:'))
        conn_layout.addWidget(self.combo_ports, 1)
        conn_layout.addWidget(self.btn_connect)
        layout.addLayout(conn_layout)

        # 2. Bảng dữ liệu 9 cột giá trị đo
        self.table = QTableWidget(125, 10)
        self.table.verticalHeader().setVisible(False)
        headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(125):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        layout.addWidget(self.table)

        # 3. Nút điều khiển
        btn_layout = QHBoxLayout()
        self.btn_step1 = QPushButton('ĐO L-Q (x,y,z)')
        self.btn_step1.clicked.connect(self.measure_lq_xyz)
        self.btn_step1.setFixedHeight(50)
        self.btn_step1.setStyleSheet("background-color: #e3f2fd; font-weight: bold;")

        self.btn_step2 = QPushButton('ĐO R (x,y,z)')
        self.btn_step2.clicked.connect(self.measure_r_xyz)
        self.btn_step2.setFixedHeight(50)
        self.btn_step2.setStyleSheet("background-color: #f1f8e9; font-weight: bold;")

        btn_layout.addWidget(self.btn_step1)
        btn_layout.addWidget(self.btn_step2)
        layout.addLayout(btn_layout)

        self.btn_export = QPushButton('XUẤT FILE CSV')
        self.btn_export.clicked.connect(self.export_csv)
        layout.addWidget(self.btn_export)

        self.lbl_status = QLabel('Trạng thái: Sẵn sàng. Nhấn kết nối để bắt đầu.')
        layout.addWidget(self.lbl_status)

        self.setLayout(layout)

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=2)
                self.btn_connect.setText("Ngắt kết nối")
                self.lbl_status.setText("Đã kết nối.")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else:
            self.ser.close()
            self.ser = None
            self.btn_connect.setText("Kết nối")

    def get_data(self):
        """Gửi lệnh trigger và đọc dữ liệu từ máy"""
        self.ser.write(b":MEAS:TRIGger\n")
        time.sleep(0.2)
        return self.ser.readline().decode('ascii').strip()

    def measure_lq_xyz(self):
        """Đo Lx Qx, sau đó Ly Qy, sau đó Lz Qz cho linh kiện hiện tại"""
        if not self.ser: return
        try:
            # Cấu hình đo L-Q
            self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
            
            # Thực hiện 3 lần đo liên tiếp cho x, y, z
            for i in range(3):
                self.lbl_status.setText(f"Đang đo L-Q lần {i+1}/3 cho LK {self.current_row+1}...")
                QApplication.processEvents() # Cập nhật giao diện
                
                res = self.get_data()
                if res:
                    parts = res.split(',')
                    # Cột 1-2 là Lx Qx, 3-4 là Ly Qy, 5-6 là Lz Qz (tính từ cột index 1 của bảng)
                    self.table.setItem(self.current_row, 1 + (i*2), QTableWidgetItem(parts[0]))
                    self.table.setItem(self.current_row, 2 + (i*2), QTableWidgetItem(parts[1]))
                time.sleep(0.5) # Nghỉ giữa các lần đo x, y, z

            self.current_row += 1
            if self.current_row < 125: self.table.selectRow(self.current_row)
            self.lbl_status.setText(f"Xong LK {self.current_row}. Sẵn sàng đo tiếp.")
        except Exception as e: self.lbl_status.setText(f"Lỗi: {e}")

    def measure_r_xyz(self):
        """Đo Rx, Ry, Rz cho linh kiện hiện tại"""
        if not self.ser: return
        if self.current_row >= 125: self.current_row = 0 # Reset về dòng 1 nếu bắt đầu lượt 2
        
        try:
            # Cấu hình đo R
            self.ser.write(b":MEAS:FUNC1 R\n:MEAS:FUNC2 NONE\n")
            
            for i in range(3):
                self.lbl_status.setText(f"Đang đo R lần {i+1}/3 cho LK {self.current_row+1}...")
                QApplication.processEvents()
                
                res = self.get_data()
                if res:
                    parts = res.split(',')
                    # Cột 7, 8, 9 trong bảng (index 7, 8, 9)
                    self.table.setItem(self.current_row, 7 + i, QTableWidgetItem(parts[0]))
                time.sleep(0.5)

            self.current_row += 1
            if self.current_row < 125: self.table.selectRow(self.current_row)
            self.lbl_status.setText(f"Xong lượt R cho LK {self.current_row}.")
        except Exception as e: self.lbl_status.setText(f"Lỗi: {e}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz'])
                for r in range(125):
                    row_data = []
                    for c in range(10):
                        item = self.table.item(r, c)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Xong", "Đã xuất file.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRApp(); ex.show()
    sys.exit(app.exec_())