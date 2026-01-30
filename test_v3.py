import sys
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox)
from PyQt5.QtGui import QColor

# --- DỮ LIỆU SPECS (Giữ nguyên đầy đủ) ---
SPECS_DATA = {
    "3DC11-4": {
        "X-10014-003": {"L": {"x":[4.56, 4.7, 4.84], "y":[4.56, 4.7, 4.84], "z":[5.53, 5.7, 5.87]}, "Q": {"x":23, "y":23, "z":19}, "R": {"x":[72, 80, 88], "y":[81.45, 90.5, 99.55], "z":[149.4, 166, 182.6]}},
        "X-10014-003R1": {"L": {"x":[4.56, 4.7, 4.84], "y":[4.56, 4.7, 4.84], "z":[5.53, 5.7, 5.87]}, "Q": {"x":23, "y":23, "z":19}, "R": {"x":[72, 80, 88], "y":[81.45, 90.5, 99.55], "z":[149.4, 166, 182.6]}},
        "X-D0287-044R2": {"L": {"x":[4.56, 4.77, 5.01], "y":[4.56, 4.77, 5.01], "z":[4.56, 4.77, 5.01]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "X-D0287-087": {"L": {"x":[4.56, 4.77, 5], "y":[4.56, 4.77, 5], "z":[4.56, 4.77, 5]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121, 135, 149]}},
        "X-13830-001": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "3DC11LP-0720J": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 155], "y":[144, 160, 176], "z":[181, 190, 199]}},
        "X-10101-058R1": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-14613-002": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-13942-002": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-12702-008": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-14012-001": {"L": {"x":[4.3, 4.77, 5.24], "y":[4.3, 4.77, 5.24], "z":[4.3, 4.77, 5.24]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "X-W0113-068": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
        "3DC11LPS-0470J": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
        "3DC11LP-0477J": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[4.53, 4.77, 5.01]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "3DC11LPS-LC-0470": {"L": {"x":[4.46, 4.7, 4.94], "y":[4.46, 4.7, 4.94], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z": 18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
        "X-14228-003": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}, "R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-12190-001": {"L": {"x":[4.63, 4.77, 4.91], "y":[4.63, 4.77, 4.91], "z":[4.63, 4.77, 4.91]}, "Q": {"x":18, "y":18, "z":18}, "R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
    }
}

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.last_selected_row = 0
        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('QC Measurement - TWO TEST MODE (L-Q & Rdc)')
        self.resize(1300, 800)
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.combo_ports = QComboBox()
        self.btn_connect = QPushButton('Kết nối COM')
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.combo_line = QComboBox()
        self.combo_line.addItems(SPECS_DATA.keys())
        self.combo_line.currentTextChanged.connect(self.update_part_numbers)
        
        self.combo_part = QComboBox()
        self.update_part_numbers()

        top_layout.addWidget(QLabel('Cổng:'))
        top_layout.addWidget(self.combo_ports)
        top_layout.addWidget(self.btn_connect)
        top_layout.addWidget(QLabel('| Line:'))
        top_layout.addWidget(self.combo_line)
        top_layout.addWidget(QLabel('Mã PART:'))
        top_layout.addWidget(self.combo_part, 1)
        layout.addLayout(top_layout)

        self.table = QTableWidget(125, 11)
        self.table.verticalHeader().setVisible(False) 
        headers = ['STT', 'Lx (mH)', 'Qx', 'Ly (mH)', 'Qy', 'Lz (mH)', 'Qz', 'Rx (Ω)', 'Ry (Ω)', 'Rz (Ω)', 'STATUS']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(125):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        
        self.table.itemClicked.connect(self.update_last_row)
        layout.addWidget(self.table)

        self.btn_start = QPushButton('BẮT ĐẦU ĐO TWO-TEST (L-Q + Rdc)')
        self.btn_start.setFixedHeight(60)
        self.btn_start.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; font-size: 14pt;")
        self.btn_start.clicked.connect(self.start_two_test_measure)
        layout.addWidget(self.btn_start)

        self.lbl_status = QLabel('Trạng thái: Sẵn sàng.')
        layout.addWidget(self.lbl_status)
        self.setLayout(layout)

    def update_last_row(self, item):
        self.last_selected_row = item.row()

    def update_part_numbers(self):
        line = self.combo_line.currentText()
        self.combo_part.clear()
        if line in SPECS_DATA:
            self.combo_part.addItems(SPECS_DATA[line].keys())

    def get_current_specs(self):
        line = self.combo_line.currentText()
        part = self.combo_part.currentText()
        return SPECS_DATA.get(line, {}).get(part, None)

    def evaluate_logic(self, val, spec_range, is_q=False):
        try:
            v = float(val)
            if is_q:
                return ("PASS", QColor(200, 255, 200)) if v >= spec_range else ("FAIL", QColor(255, 150, 150))
            low, center, high = spec_range
            if v < low or v > high: return "FAIL", QColor(255, 50, 50)
            margin = (high - low) * 0.02
            if v < (low + margin) or v > (high - margin): return "WARNING", QColor(255, 255, 150)
            return "PASS", QColor(150, 255, 150)
        except: return "ERROR", QColor(255, 255, 255)

    def start_two_test_measure(self):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Lỗi", "Hãy kết nối cổng COM trước!")
            return
        
        specs = self.get_current_specs()
        if not specs: return

        try:
            # --- CẤU HÌNH TWO TEST MODE TRÊN MÁY ---
            self.ser.write(b":MEAS:NUM-OF-TESTS 2\n") # Bật 2 bài đo [cite: 1923]
            time.sleep(0.1)
            self.ser.write(b":MEAS:TEST 1\n:MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n") # Test 1: L-Q [cite: 1952, 1999]
            time.sleep(0.1)
            self.ser.write(b":MEAS:TEST 2\n:MEAS:FUNC1 Rdc\n") # Test 2: Rdc [cite: 1952, 1999]
            time.sleep(0.2)

            for row in range(self.last_selected_row, 125):
                self.table.selectRow(row)
                self.last_selected_row = row
                row_evals = []

                axes = ['x', 'y', 'z']
                for i, axis in enumerate(axes):
                    valid = False
                    while not valid:
                        self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: CHÂM KIM ĐO...")
                        QApplication.processEvents()
                        
                        self.ser.reset_input_buffer() 
                        self.ser.write(b":MEAS:TRIGger\n") # Kích hoạt đo cả 2 Test [cite: 1899]
                        time.sleep(0.15) # Rdc cần thời gian đo lâu hơn AC [cite: 2337]
                        res = self.ser.readline().decode('ascii').strip()
                        
                        # Phản hồi Two Test có dạng: t1f1, t1f2, t2f1 (L, Q, R) [cite: 1911]
                        if res and ',' in res:
                            try:
                                parts = res.split(',')
                                val_l_raw = float(parts[0])
                                val_q = float(parts[1])
                                val_r = float(parts[2])

                                # Lọc chạm kim (Dựa trên L và Q)
                                if 0 < val_l_raw < 0.5 and val_q > 0.1:
                                    val_mh = val_l_raw * 1000 # Đổi sang mH
                                    
                                    # So sánh và điền L-Q
                                    l_st, l_c = self.evaluate_logic(val_mh, specs["L"][axis])
                                    q_st, q_c = self.evaluate_logic(val_q, specs["Q"][axis], is_q=True)
                                    self.table.setItem(row, 1+i*2, QTableWidgetItem(f"{val_mh:.4f}"))
                                    self.table.item(row, 1+i*2).setBackground(l_c)
                                    self.table.setItem(row, 2+i*2, QTableWidgetItem(f"{val_q:.2f}"))
                                    self.table.item(row, 2+i*2).setBackground(q_c)
                                    
                                    # So sánh và điền R (Cột 7, 8, 9)
                                    r_st, r_c = self.evaluate_logic(val_r, specs["R"][axis])
                                    self.table.setItem(row, 7+i, QTableWidgetItem(f"{val_r:.2f}"))
                                    self.table.item(row, 7+i).setBackground(r_c)
                                    
                                    row_evals.extend([l_st, q_st, r_st])
                                    valid = True
                            except: continue

                    # Chờ rút kim
                    released = False
                    while not released:
                        self.lbl_status.setText(f"XONG {axis.upper()}. RÚT KIM RA!")
                        QApplication.processEvents()
                        self.ser.write(b":MEAS:TRIGger\n")
                        time.sleep(0.05)
                        res_rel = self.ser.readline().decode('ascii').strip()
                        try:
                            if ',' in res_rel:
                                v_check = float(res_rel.split(',')[0])
                                if v_check > 0.5 or v_check <= 0: released = True
                            else: released = True
                        except: released = True

                # Cập nhật STATUS tổng kết (Cột 10)
                if row_evals:
                    final_s = "PASS"
                    bg = QColor(150, 255, 150)
                    if "FAIL" in row_evals: final_s = "FAIL"; bg = QColor(255, 150, 150)
                    elif "WARNING" in row_evals: final_s = "WARNING"; bg = QColor(255, 255, 180)
                    s_item = QTableWidgetItem(final_s)
                    s_item.setBackground(bg)
                    self.table.setItem(row, 10, s_item)

            QMessageBox.information(self, "Xong", "Đã đo hoàn tất danh sách.")
        except Exception as e: self.lbl_status.setText(f"Lỗi: {str(e)}")

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
                self.btn_connect.setText("Ngắt kết nối")
                self.lbl_status.setText("REMOTE MODE.")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else:
            try:
                self.ser.write(b":SYSTem:LOCal\n") # Trả về Local để dùng phím máy [cite: 342, 349]
                time.sleep(0.2); self.ser.close()
            except: pass
            self.ser = None
            self.btn_connect.setText("Kết nối COM")
            self.lbl_status.setText("LOCAL MODE.")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRApp(); ex.show()
    sys.exit(app.exec_())