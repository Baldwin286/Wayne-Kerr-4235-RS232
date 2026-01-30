import sys
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox)
from PyQt5.QtGui import QColor

# --- DỮ LIỆU SPECS ---
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
        self.setWindowTitle('QC Measurement System - Wayne Kerr 4235')
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
        headers = ['STT', 'Lx (mH)', 'Qx', 'Ly (mH)', 'Qy', 'Lz (mH)', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(125):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        
        self.table.itemClicked.connect(self.update_last_row)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_lq = QPushButton('ĐO L-Q TỰ ĐỘNG')
        self.btn_lq.clicked.connect(lambda: self.auto_measure_process("LQ"))
        self.btn_r = QPushButton('ĐO R TỰ ĐỘNG')
        self.btn_r.clicked.connect(lambda: self.auto_measure_process("R"))
        
        self.btn_lq.setFixedHeight(50)
        self.btn_r.setFixedHeight(50)
        btn_layout.addWidget(self.btn_lq)
        btn_layout.addWidget(self.btn_r)
        layout.addLayout(btn_layout)

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
                # Q >= Q_min là PASS
                return ("PASS", QColor(200, 255, 200)) if v >= spec_range else ("FAIL", QColor(255, 150, 150))
            
            # Logic cho L và R: [Low, Center, High]
            low, center, high = spec_range
            if v < low or v > high: return "FAIL", QColor(255, 50, 50)
            
            # Warning: 2% sát biên
            margin = (high - low) * 0.02
            if v < (low + margin) or v > (high - margin): return "WARNING", QColor(255, 255, 150)
            
            return "PASS", QColor(150, 255, 150)
        except: return "ERROR", QColor(255, 255, 255)

    def auto_measure_process(self, mode):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối cổng COM!")
            return
        
        specs = self.get_current_specs()
        if not specs: return

        # Bắt đầu từ dòng đang được chọn hoặc đo dở
        start_row = self.last_selected_row
        
        L_MAX_LIMIT_H = 0.5 
        Q_MIN_STABLE = 0.1
        R_MAX_LIMIT = 5000.0

        try:
            for row in range(start_row, 125):
                self.table.selectRow(row)
                self.last_selected_row = row
                
                axes = ['x', 'y', 'z']
                for i, axis in enumerate(axes):
                    valid = False
                    while not valid:
                        mode_text = "L-Q" if mode == "LQ" else "R"
                        self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: CHÂM KIM ({mode_text})")
                        self.lbl_status.setStyleSheet("color: blue; font-weight: bold;")
                        QApplication.processEvents()
                        
                        self.ser.reset_input_buffer() 
                        self.ser.write(b":MEAS:TRIGger\n")
                        time.sleep(0.06) 
                        res = self.ser.readline().decode('ascii').strip()
                        
                        if ',' in res:
                            try:
                                parts = res.split(',')
                                val_primary = float(parts[0]) 
                                
                                if mode == "LQ":
                                    val_q = float(parts[1])
                                    if 0 < val_primary < L_MAX_LIMIT_H and val_q > Q_MIN_STABLE:
                                        val_mh = val_primary * 1000 
                                        st, color = self.evaluate_logic(val_mh, specs["L"][axis])
                                        q_st, q_color = self.evaluate_logic(val_q, specs["Q"][axis], is_q=True)
                                        
                                        # Lưu L
                                        it_l = QTableWidgetItem(f"{val_mh:.4f}")
                                        it_l.setBackground(color)
                                        self.table.setItem(row, 1 + i*2, it_l)
                                        
                                        # Lưu Q
                                        it_q = QTableWidgetItem(f"{val_q:.2f}")
                                        it_q.setBackground(q_color)
                                        self.table.setItem(row, 2 + i*2, it_q)
                                        valid = True
                                else: # MODE ĐO R
                                    if 0 < val_primary < R_MAX_LIMIT:
                                        # --- SO SÁNH R VỚI SPECS ---
                                        st, color = self.evaluate_logic(val_primary, specs["R"][axis])
                                        
                                        # Lưu R vào cột 7, 8, 9 và đổi màu nền ô đó
                                        it_r = QTableWidgetItem(f"{val_primary:.2f}")
                                        it_r.setBackground(color)
                                        self.table.setItem(row, 7 + i, it_r)
                                        valid = True
                            except: continue

                    # Chờ rút kim
                    released = False
                    while not released:
                        self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: RÚT KIM!")
                        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
                        QApplication.processEvents()
                        self.ser.write(b":MEAS:TRIGger\n")
                        time.sleep(0.03)
                        res_rel = self.ser.readline().decode('ascii').strip()
                        try:
                            if ',' in res_rel:
                                v = float(res_rel.split(',')[0])
                                if mode == "LQ":
                                    if v > L_MAX_LIMIT_H or v <= 0: released = True
                                else:
                                    if v > R_MAX_LIMIT or v <= 0: released = True
                            else: released = True
                        except: released = True

                # Cập nhật STATUS tổng kết cột 10 (PASS/FAIL/WARNING)
                self.update_row_status(row, specs)

            QMessageBox.information(self, "Xong", "Đã đo hoàn tất danh sách.")
        except Exception as e:
            self.lbl_status.setText(f"Lỗi: {str(e)}")

    def update_row_status(self, row, specs):
        """Quét lại toàn bộ các ô đã đo trên dòng để đưa ra kết luận STATUS cuối cùng"""
        all_results = []
        axes = ['x', 'y', 'z']
        
        # Kiểm tra Lx, Ly, Lz (Cột 1, 3, 5)
        for i, col in enumerate([1, 3, 5]):
            it = self.table.item(row, col)
            if it and it.text() != "":
                all_results.append(self.evaluate_logic(it.text(), specs["L"][axes[i]])[0])
        
        # Kiểm tra Qx, Qy, Qz (Cột 2, 4, 6)
        for i, col in enumerate([2, 4, 6]):
            it = self.table.item(row, col)
            if it and it.text() != "":
                all_results.append(self.evaluate_logic(it.text(), specs["Q"][axes[i]], is_q=True)[0])
        
        # Kiểm tra Rx, Ry, Rz (Cột 7, 8, 9)
        for i, col in enumerate([7, 8, 9]):
            it = self.table.item(row, col)
            if it and it.text() != "":
                all_results.append(self.evaluate_logic(it.text(), specs["R"][axes[i]])[0])

        if all_results:
            final_s = "PASS"
            final_bg = QColor(150, 255, 150)
            if "FAIL" in all_results:
                final_s = "FAIL"; final_bg = QColor(255, 150, 150)
            elif "WARNING" in all_results:
                final_s = "WARNING"; final_bg = QColor(255, 255, 180)
            
            s_item = QTableWidgetItem(final_s)
            s_item.setBackground(final_bg)
            self.table.setItem(row, 10, s_item)

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
                self.btn_connect.setText("Ngắt kết nối")
                self.btn_connect.setStyleSheet("background-color: #ffcdd2;")
                self.lbl_status.setText("Đã kết nối REMOTE.")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else:
            try:
                self.ser.write(b":SYSTem:LOCal\n")
                time.sleep(0.2); self.ser.close()
            except: pass
            self.ser = None
            self.btn_connect.setText("Kết nối COM")
            self.btn_connect.setStyleSheet("")
            self.lbl_status.setText("Máy đo đã về LOCAL.")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

    def closeEvent(self, event):
        if self.ser and self.ser.is_open:
            try: self.ser.write(b":SYSTem:LOCal\n"); time.sleep(0.1); self.ser.close()
            except: pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRApp(); ex.show()
    sys.exit(app.exec_())