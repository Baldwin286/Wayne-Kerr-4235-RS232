import sys
import serial
import serial.tools.list_ports
import time
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog)
from PyQt5.QtGui import QColor, QFont

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.current_row = 0
        
        # --- CẤU HÌNH BỘ LỌC LINH KIỆN ---
        self.L_MIN_DETECT = 1e-9  # Ngưỡng phát hiện

        # --- THIẾT LẬP NGƯỠNG KIỂM TRA ---
        self.CENTER = 100e-6  # Giá trị lý tưởng 
        self.UPPER = 110e-6   # Trên mức này là FAIL
        self.LOWER = 90e-6    # Dưới mức này là FAIL 
        # Vùng Warning: Nằm trong khoảng 2% sát biên Upper hoặc Lower
        self.WARN_ZONE = 2e-6 

        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('Wayne Kerr 4235 - QC Measurement')
        self.resize(1300, 750)
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

        # 2. Bảng dữ liệu (Ẩn STT mặc định, STT tự tạo ở cột 0, STATUS ở cột 10)
        self.table = QTableWidget(125, 11)
        self.table.verticalHeader().setVisible(False)
        headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(125):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        layout.addWidget(self.table)

        # 3. Nút điều khiển
        btn_layout = QHBoxLayout()
        self.btn_step1 = QPushButton('ĐO L-Q (x,y,z)')
        self.btn_step1.clicked.connect(self.measure_lq_xyz)
        self.btn_step1.setFixedHeight(60)
        self.btn_step1.setStyleSheet("background-color: #e3f2fd; font-weight: bold; font-size: 12pt;")

        self.btn_step2 = QPushButton('ĐO R (x,y,z)')
        self.btn_step2.clicked.connect(self.measure_r_xyz)
        self.btn_step2.setFixedHeight(60)
        self.btn_step2.setStyleSheet("background-color: #f1f8e9; font-weight: bold; font-size: 12pt;")

        btn_layout.addWidget(self.btn_step1)
        btn_layout.addWidget(self.btn_step2)
        layout.addLayout(btn_layout)

        self.btn_export = QPushButton('XUẤT FILE CSV')
        self.btn_export.clicked.connect(self.export_csv)
        layout.addWidget(self.btn_export)

        self.lbl_status = QLabel('Trạng thái: Sẵn sàng.')
        layout.addWidget(self.lbl_status)

        self.setLayout(layout)

    def evaluate_value(self, val_str):
        """Hàm so sánh giá trị với các ngưỡng Center, Upper, Lower"""
        try:
            val = float(val_str)
            # Kiểm tra FAIL
            if val < self.LOWER or val > self.UPPER:
                return "FAIL", QColor(255, 0, 0) # Chữ đỏ hoặc nền đỏ
            # Kiểm tra WARNING (nằm gần sát biên)
            elif (val < self.LOWER + self.WARN_ZONE) or (val > self.UPPER - self.WARN_ZONE):
                return "WARNING", QColor(255, 255, 0) # Vàng
            # Còn lại là PASS
            else:
                return "PASS", QColor(0, 255, 0) # Xanh lá
        except:
            return "N/A", QColor(255, 255, 255)

    def measure_lq_xyz(self):
        if not self.ser: return
        try:
            self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
            
            results_in_row = []
            for i in range(3):
                self.lbl_status.setText(f"Đang đo lần {i+1}/3 cho LK {self.current_row+1}...")
                QApplication.processEvents()
                
                self.ser.write(b":MEAS:TRIGger\n")
                time.sleep(0.4)
                res = self.ser.readline().decode('ascii').strip()
                
                if res and ',' in res:
                    parts = res.split(',')
                    l_val = parts[0]
                    q_val = parts[1]
                    
                    # Ghi vào bảng
                    self.table.setItem(self.current_row, 1 + (i*2), QTableWidgetItem(l_val))
                    self.table.setItem(self.current_row, 2 + (i*2), QTableWidgetItem(q_val))
                    
                    # Đánh giá giá trị L vừa đo
                    status, _ = self.evaluate_value(l_val)
                    results_in_row.append(status)

            # --- TÍNH TOÁN STATUS TỔNG HỢP CHO DÒNG ---
            final_status = "PASS"
            final_color = QColor(0, 255, 0) # Mặc định xanh lá
            
            if "FAIL" in results_in_row:
                final_status = "FAIL"
                final_color = QColor(255, 0, 0) # Đỏ
            elif "WARNING" in results_in_row:
                final_status = "WARNING"
                final_color = QColor(255, 255, 0) # Vàng
            
            # Điền vào cột STATUS (Cột index 10)
            status_item = QTableWidgetItem(final_status)
            status_item.setBackground(final_color)
            status_item.setTextAlignment(0x0004 | 0x0080) # Căn giữa
            self.table.setItem(self.current_row, 10, status_item)

            self.current_row += 1
            if self.current_row < 125: self.table.selectRow(self.current_row)
            self.lbl_status.setText(f"Xong LK {self.current_row}. Kết quả: {final_status}")
            
        except Exception as e: self.lbl_status.setText(f"Lỗi: {e}")

    def measure_r_xyz(self):
        # Logic đo R tương tự nhưng điền vào cột 7, 8, 9
        if not self.ser: return
        if self.current_row >= 125: self.current_row = 0
        try:
            self.ser.write(b":MEAS:FUNC1 R\n:MEAS:FUNC2 NONE\n")
            for i in range(3):
                self.ser.write(b":MEAS:TRIGger\n")
                time.sleep(0.4)
                res = self.ser.readline().decode('ascii').strip()
                if res:
                    self.table.setItem(self.current_row, 7 + i, QTableWidgetItem(res.split(',')[0]))
            self.current_row += 1
            if self.current_row < 125: self.table.selectRow(self.current_row)
        except Exception as e: self.lbl_status.setText(f"Lỗi: {e}")

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=2)
                self.btn_connect.setText("Ngắt kết nối")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else:
            self.ser.close()
            self.ser = None
            self.btn_connect.setText("Kết nối")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS'])
                for r in range(125):
                    row_data = []
                    for c in range(11):
                        item = self.table.item(r, c)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Xong", "Đã xuất file dữ liệu.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRApp(); ex.show()
    sys.exit(app.exec_())