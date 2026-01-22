import sys
import serial
import serial.tools.list_ports
import time
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog)
from PyQt5.QtGui import QColor

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.current_row = 0
        
        # --- CẤU HÌNH BỘ LỌC LINH KIỆN ---
        self.L_MIN_DETECT = 1e-9  # Ngưỡng phát hiện (Ví dụ: > 1nH mới coi là đã kẹp kim)
        self.L_CENTER = 100e-6    # 100uH
        self.L_UPPER = 110e-6
        self.L_LOWER = 90e-6
        self.L_WARN_MARGIN = 2e-6

        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('Wayne Kerr 4300 - Bộ lọc kẹp linh kiện thông minh')
        self.resize(1200, 750)
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

        # 2. Bảng dữ liệu (11 cột: STT, Lx, Qx, Ly, Qy, Lz, Qz, Rx, Ry, Rz, STATUS)
        self.table = QTableWidget(125, 11)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalHeaderLabels(['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(125):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        layout.addWidget(self.table)

        # 3. Nút bấm chế độ
        self.btn_measure = QPushButton('BẮT ĐẦU QUÉT VÀ ĐO (Lx Qx Ly Qy Lz Qz)')
        self.btn_measure.setFixedHeight(70)
        self.btn_measure.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold; font-size: 14pt;")
        self.btn_measure.clicked.connect(self.smart_measure_flow)
        layout.addWidget(self.btn_measure)

        self.lbl_msg = QLabel('Trạng thái: Đang chờ...')
        self.lbl_msg.setStyleSheet("font-size: 12pt; color: darkblue;")
        layout.addWidget(self.lbl_msg)

        self.setLayout(layout)

    def evaluate_status(self, val):
        try:
            v = float(val)
            if v < self.L_LOWER or v > self.L_UPPER: return "FAIL", QColor(255, 0, 0)
            if (v < self.L_LOWER + self.L_LOWER*0.02) or (v > self.L_UPPER - self.L_UPPER*0.02):
                return "WARNING", QColor(255, 255, 0)
            return "PASS", QColor(0, 255, 0)
        except: return "N/A", QColor(255, 255, 255)

    def smart_measure_flow(self):
        """Quy trình đo thông minh: Chờ kẹp -> Đo x -> Chờ rút -> Chờ kẹp -> Đo y..."""
        if not self.ser: return
        
        try:
            self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
            
            # Danh sách các cột cần điền cho x, y, z (Lx Qx là cột 1,2; Ly Qy là 3,4; Lz Qz là 5,6)
            steps = [1, 3, 5] 
            names = ['x', 'y', 'z']
            row_results = []

            for idx, col_start in enumerate(steps):
                self.lbl_msg.setText(f"LK {self.current_row+1}: HÃY KẸP KIM ĐO CHO VỊ TRÍ {names[idx].upper()}")
                self.lbl_msg.setStyleSheet("color: red; font-weight: bold;")
                QApplication.processEvents()

                # --- VÒNG LẶP CHỜ KẸP LINH KIỆN ---
                while True:
                    self.ser.write(b":MEAS:TRIGger\n")
                    time.sleep(0.2)
                    data = self.ser.readline().decode('ascii').strip()
                    if data and ',' in data:
                        val_l = float(data.split(',')[0])
                        if val_l > self.L_MIN_DETECT: # ĐÃ PHÁT HIỆN KẸP THẬT
                            time.sleep(0.3) # Đợi ổn định tiếp xúc
                            # Đo lại lần cuối để lấy số chuẩn
                            self.ser.write(b":MEAS:TRIGger\n")
                            final_data = self.ser.readline().decode('ascii').strip()
                            l_final, q_final = final_data.split(',')
                            
                            # Ghi vào bảng
                            self.table.setItem(self.current_row, col_start, QTableWidgetItem(l_final))
                            self.table.setItem(self.current_row, col_start + 1, QTableWidgetItem(q_final))
                            
                            # Đánh giá status
                            st, color = self.evaluate_status(l_final)
                            self.table.item(self.current_row, col_start).setBackground(color)
                            row_results.append(st)
                            break
                    QApplication.processEvents()

                self.lbl_msg.setText(f"Xong {names[idx].upper()}. HÃY RÚT KIM RA!")
                self.lbl_msg.setStyleSheet("color: blue;")
                
                # --- VÒNG LẶP CHỜ RÚT KIM (Để tránh đo trùng) ---
                while True:
                    self.ser.write(b":MEAS:TRIGger\n")
                    time.sleep(0.2)
                    data = self.ser.readline().decode('ascii').strip()
                    if data and ',' in data:
                        if float(data.split(',')[0]) < self.L_MIN_DETECT: # Đã rút kim
                            break
                    QApplication.processEvents()

            # Tổng hợp STATUS cuối cùng cho linh kiện
            final_st = "PASS"
            if "FAIL" in row_results: final_st = "FAIL"
            elif "WARNING" in row_results: final_st = "WARNING"
            
            item_st = QTableWidgetItem(final_st)
            if final_st == "FAIL": item_st.setBackground(QColor(255, 0, 0))
            elif final_st == "WARNING": item_st.setBackground(QColor(255, 255, 0))
            else: item_st.setBackground(QColor(0, 255, 0))
            self.table.setItem(self.current_row, 10, item_st)

            self.current_row += 1
            if self.current_row < 125: self.table.selectRow(self.current_row)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
                self.btn_connect.setText("Ngắt kết nối")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else:
            self.ser.close()
            self.ser = None
            self.btn_connect.setText("Kết nối")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRApp(); ex.show()
    sys.exit(app.exec_())