# import sys
# import serial
# import serial.tools.list_ports
# import time
# import csv
# import re
# from datetime import datetime
# from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
#                              QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
#                              QHBoxLayout, QHeaderView, QMessageBox, QFileDialog)
# from PyQt5.QtGui import QColor

# # --- DỮ LIỆU SPECS ---
# SPECS_DATA = {
#     "3DC11-4": {
#         "X-10014-003": {"L": {"x":[4.56, 4.7, 4.84], "y":[4.56, 4.7, 4.84], "z":[5.53, 5.7, 5.87]}, "Q": {"x":23, "y":23, "z":19}},
#         "X-10014-003R1": {"L": {"x":[4.56, 4.7, 4.84], "y":[4.56, 4.7, 4.84], "z":[5.53, 5.7, 5.87]}, "Q": {"x":23, "y":23, "z":19}},
#         "X-D0287-044R2": {"L": {"x":[4.56, 4.77, 5.01], "y":[4.56, 4.77, 5.01], "z":[4.56, 4.77, 5.01]}, "Q": {"x":18, "y":18, "z":18}},
#         "X-D0287-087": {"L": {"x":[4.56, 4.77, 5], "y":[4.56, 4.77, 5], "z":[4.56, 4.77, 5]}, "Q": {"x":18, "y":18, "z":18}},
#         "X-13830-001": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "3DC11LP-0720J": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "X-10101-058R1": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "X-14613-002": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "X-13942-002": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "X-12702-008": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "X-14012-001": {"L": {"x":[4.3, 4.77, 5.24], "y":[4.3, 4.77, 5.24], "z":[4.3, 4.77, 5.24]}, "Q": {"x":18, "y":18, "z":18}},
#         "X-W0113-068": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z":18}},
#         "3DC11LPS-0470J": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z":18}},
#         "3DC11LP-0477J": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[4.53, 4.77, 5.01]}, "Q": {"x":18, "y":18, "z":18}},
#         "3DC11LPS-LC-0470": {"L": {"x":[4.46, 4.7, 4.94], "y":[4.46, 4.7, 4.94], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z": 18}},
#         "X-14228-003": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
#         "X-12190-001": {"L": {"x":[4.63, 4.77, 4.91], "y":[4.63, 4.77, 4.91], "z":[4.63, 4.77, 4.91]}, "Q": {"x":18, "y":18, "z":18}},
#     }
# }

# class LCRApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.ser = None
#         self.last_selected_row = 0
#         self.initUI()
#         self.refresh_ports()

#     def initUI(self):
#         self.setWindowTitle('QC Measurement - L-Q Only')
#         self.resize(1100, 800)
#         layout = QVBoxLayout()

#         # 1. Cấu hình COM và Lựa chọn Line/Part
#         top_layout = QHBoxLayout()
#         self.combo_ports = QComboBox()
#         self.btn_connect = QPushButton('Kết nối COM')
#         self.btn_connect.clicked.connect(self.toggle_connection)
        
#         self.combo_line = QComboBox()
#         self.combo_line.addItems(SPECS_DATA.keys())
#         self.combo_line.currentTextChanged.connect(self.update_part_numbers)
        
#         self.combo_part = QComboBox()
#         self.update_part_numbers()

#         top_layout.addWidget(QLabel('Cổng:'))
#         top_layout.addWidget(self.combo_ports)
#         top_layout.addWidget(self.btn_connect)
#         top_layout.addWidget(QLabel('| Line:'))
#         top_layout.addWidget(self.combo_line)
#         top_layout.addWidget(QLabel('Mã PART:'))
#         top_layout.addWidget(self.combo_part, 1)
#         layout.addLayout(top_layout)

#         # 2. Bảng dữ liệu (8 cột: STT, Lx, Qx, Ly, Qy, Lz, Qz, STATUS)
#         self.table = QTableWidget(125, 8)
#         self.table.verticalHeader().setVisible(False) 
#         headers = ['STT', 'Lx (mH)', 'Qx', 'Ly (mH)', 'Qy', 'Lz (mH)', 'Qz', 'STATUS']
#         self.table.setHorizontalHeaderLabels(headers)
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#         for i in range(125):
#             self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        
#         self.table.itemClicked.connect(self.update_last_row)
#         layout.addWidget(self.table)

#         # 3. Nút chức năng
#         btn_layout = QHBoxLayout()
#         self.btn_lq = QPushButton('ĐO L-Q TỰ ĐỘNG (125 MẪU)')
#         self.btn_lq.setFixedHeight(50)
#         self.btn_lq.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
#         self.btn_lq.clicked.connect(self.auto_measure_process)
        
#         self.btn_export = QPushButton('XUẤT FILE CSV')
#         self.btn_export.setFixedHeight(50)
#         self.btn_export.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
#         self.btn_export.clicked.connect(self.export_csv)

#         btn_layout.addWidget(self.btn_lq)
#         btn_layout.addWidget(self.btn_export)
#         layout.addLayout(btn_layout)

#         self.lbl_status = QLabel('Trạng thái: Sẵn sàng.')
#         layout.addWidget(self.lbl_status)
#         self.setLayout(layout)

#     # --- CÁC HÀM BỔ SUNG ĐỂ SỬA LỖI ---
#     def update_last_row(self, item):
#         self.last_selected_row = item.row()

#     def update_part_numbers(self):
#         line = self.combo_line.currentText()
#         self.combo_part.clear()
#         if line in SPECS_DATA:
#             self.combo_part.addItems(SPECS_DATA[line].keys())

#     def get_current_specs(self):
#         line = self.combo_line.currentText()
#         part = self.combo_part.currentText()
#         return SPECS_DATA.get(line, {}).get(part, None)

#     def evaluate_logic(self, val, spec_range, is_q=False):
#         try:
#             v = float(val)
#             if is_q:
#                 return ("PASS", QColor(200, 255, 200)) if v >= spec_range else ("FAIL", QColor(255, 150, 150))
#             low, center, high = spec_range
#             if v < low or v > high: return "FAIL", QColor(255, 50, 50)
#             margin = (high - low) * 0.02
#             if v < (low + margin) or v > (high - margin): return "WARNING", QColor(255, 255, 150)
#             return "PASS", QColor(150, 255, 150)
#         except: return "ERROR", QColor(255, 255, 255)

#     def auto_measure_process(self):
#         if not self.ser or not self.ser.is_open:
#             QMessageBox.warning(self, "Lỗi", "Chưa kết nối COM!")
#             return
        
#         specs = self.get_current_specs() # ĐÃ CÓ HÀM NÀY, KHÔNG CÒN LỖI
#         if not specs: return

#         L_MAX_LIMIT_H = 0.5 
#         Q_MIN_STABLE = 0.1

#         try:
#             self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
#             time.sleep(0.1)

#             for row in range(self.last_selected_row, 125):
#                 self.table.selectRow(row)
#                 self.last_selected_row = row
#                 row_evals = []
#                 axes = ['x', 'y', 'z']

#                 for i, axis in enumerate(axes):
#                     valid = False
#                     while not valid:
#                         self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: CHÂM KIM ĐO L-Q...")
#                         QApplication.processEvents()
#                         self.ser.reset_input_buffer() 
#                         self.ser.write(b":MEAS:TRIGger\n")
#                         time.sleep(0.06) 
#                         res = self.ser.readline().decode('ascii').strip()
                        
#                         if ',' in res:
#                             try:
#                                 parts = res.split(',')
#                                 val_l_raw = float(parts[0])
#                                 val_q = float(parts[1])
#                                 if 0 < val_l_raw < L_MAX_LIMIT_H and val_q > Q_MIN_STABLE:
#                                     val_mh = val_l_raw * 1000 
#                                     st, color = self.evaluate_logic(val_mh, specs["L"][axis])
#                                     q_st, q_color = self.evaluate_logic(val_q, specs["Q"][axis], is_q=True)
                                    
#                                     it_l = QTableWidgetItem(f"{val_mh:.4f}"); it_l.setBackground(color)
#                                     self.table.setItem(row, 1 + i*2, it_l)
#                                     it_q = QTableWidgetItem(f"{val_q:.2f}"); it_q.setBackground(q_color)
#                                     self.table.setItem(row, 2 + i*2, it_q)
#                                     row_evals.extend([st, q_st]); valid = True
#                             except: continue

#                     # Chờ rút kim
#                     released = False
#                     while not released:
#                         self.lbl_status.setText(f"XONG {axis.upper()}. RÚT KIM!")
#                         QApplication.processEvents()
#                         self.ser.write(b":MEAS:TRIGger\n")
#                         time.sleep(0.03)
#                         res_rel = self.ser.readline().decode('ascii').strip()
#                         try:
#                             if ',' in res_rel:
#                                 v = float(res_rel.split(',')[0])
#                                 if v > L_MAX_LIMIT_H or v <= 0: released = True
#                             else: released = True
#                         except: released = True

#                 if row_evals:
#                     final_s = "PASS"; bg = QColor(150, 255, 150)
#                     if "FAIL" in row_evals: final_s = "FAIL"; bg = QColor(255, 150, 150)
#                     elif "WARNING" in row_evals: final_s = "WARNING"; bg = QColor(255, 255, 180)
#                     s_item = QTableWidgetItem(final_s); s_item.setBackground(bg)
#                     self.table.setItem(row, 7, s_item)

#             QMessageBox.information(self, "Xong", "Đã đo hoàn tất.")
#         except Exception as e: self.lbl_status.setText(f"Lỗi: {str(e)}")

#     def export_csv(self):
#         line = self.combo_line.currentText()
#         part = self.combo_part.currentText()
#         # Định dạng ngày tháng năm: NgàyThángNăm (vd: 30012026)
#         date_str = datetime.now().strftime("%d%m%Y")
#         # Tên file: Line_Part_NgayThangNam.csv
#         default_filename = f"{line}_{part}_{date_str}.csv"
        
#         path, _ = QFileDialog.getSaveFileName(self, "Lưu file CSV", default_filename, "CSV Files (*.csv)")
        
#         if path:
#             try:
#                 with open(path, 'w', newline='', encoding='utf-8-sig') as file:
#                     writer = csv.writer(file)
#                     # Ghi thông tin Line và Part ở đầu file cho rõ ràng
#                     writer.writerow(["LINE", line, "PART NUMBER", part, "DATE", date_str])
#                     writer.writerow([]) # Dòng trống
#                     # Ghi tiêu đề bảng
#                     headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
#                     writer.writerow(headers)
#                     # Ghi dữ liệu đo
#                     for row in range(125):
#                         row_data = []
#                         for col in range(self.table.columnCount()):
#                             item = self.table.item(row, col)
#                             row_data.append(item.text() if item else "")
#                         if any(row_data[1:]): # Chỉ ghi những dòng có dữ liệu đo
#                             writer.writerow(row_data)
#                 QMessageBox.information(self, "Thành công", f"Đã xuất file tại: {path}")
#             except Exception as e:
#                 QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")

#     def toggle_connection(self):
#         if self.ser is None:
#             try:
#                 self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
#                 self.btn_connect.setText("Ngắt kết nối")
#                 self.btn_connect.setStyleSheet("background-color: #ffcdd2;")
#                 self.lbl_status.setText("REMOTE MODE.")
#             except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
#         else:
#             try:
#                 self.ser.write(b":SYSTem:LOCal\n")
#                 time.sleep(0.2); self.ser.close()
#             except: pass
#             self.ser = None
#             self.btn_connect.setText("Kết nối COM")
#             self.btn_connect.setStyleSheet("")
#             self.lbl_status.setText("LOCAL MODE.")

#     def refresh_ports(self):
#         self.combo_ports.clear()
#         for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = LCRApp(); ex.show()
#     sys.exit(app.exec_())

import sys
import serial
import serial.tools.list_ports
import time
import csv
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QSpinBox)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import pyqtSignal, Qt

# --- ĐƯỜNG DẪN THƯ MỤC LƯU FILE ---
SAVE_FOLDER = r"F:\TTTN\auto_measure_LCR\CSV_data\3DC_30022026" 

SPECS_DATA = {
    "3DC11-4": {
        "X-10014-003": {"L": {"x":[4.56, 4.7, 4.84], "y":[4.56, 4.7, 4.84], "z":[5.53, 5.7, 5.87]}, "Q": {"x":23, "y":23, "z":19}},
        "X-10014-003R1": {"L": {"x":[4.56, 4.7, 4.84], "y":[4.56, 4.7, 4.84], "z":[5.53, 5.7, 5.87]}, "Q": {"x":23, "y":23, "z":19}},
        "X-D0287-044R2": {"L": {"x":[4.56, 4.77, 5.01], "y":[4.56, 4.77, 5.01], "z":[4.56, 4.77, 5.01]}, "Q": {"x":18, "y":18, "z":18}},
        "X-D0287-087": {"L": {"x":[4.56, 4.77, 5], "y":[4.56, 4.77, 5], "z":[4.56, 4.77, 5]}, "Q": {"x":18, "y":18, "z":18}},
        "X-13830-001": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "3DC11LP-0720J": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "X-10101-058R1": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "X-14613-002": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "X-13942-002": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "X-12702-008": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "X-14012-001": {"L": {"x":[4.3, 4.77, 5.24], "y":[4.3, 4.77, 5.24], "z":[4.3, 4.77, 5.24]}, "Q": {"x":[18, 20, 22], "y":[18, 20, 22], "z":[18, 20, 22]}},
        "X-W0113-068": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[6.84, 7.2, 7.56]}, "Q": {"x":[18, 20, 22], "y":[18, 20, 22], "z":[18, 20, 22]}},
        "3DC11LPS-0470J": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[6.84, 7.2, 7.56]}, "Q": {"x":[18, 20, 22], "y":[18, 20, 22], "z":[18, 20, 22]}},
        "3DC11LP-0477J": {"L": {"x":[4.53, 4.77, 5.01], "y":[4.53, 4.77, 5.01], "z":[4.53, 4.77, 5.01]}, "Q": {"x":[18, 20, 22], "y":[18, 20, 22], "z":[18, 20, 22]}},
        "3DC11LPS-LC-0470": {"L": {"x":[4.46, 4.7, 4.94], "y":[4.46, 4.7, 4.94], "z":[6.84, 7.2, 7.56]}, "Q": {"x":18, "y":18, "z":18}},
        "X-14228-003": {"L": {"x":[6.84, 7.2, 7.56], "y":[6.84, 7.2, 7.56], "z":[6.84, 7.2, 7.56]}, "Q": {"x":14.5, "y":14.5, "z":18}},
        "3DC09LP-0720J": {"L": {"x":[6.84, 7.20, 7.56], "y":[6.84, 7.20, 7.56], "z":[6.84, 7.20, 7.56]}, 
                          "Q": {"x":[16.2, 18, 19.8], "y":[15.3, 17, 18.7], "z":[26.1, 29, 31.9]}},
        "X-12190-001": {"L": {"x":[4.63, 4.77, 4.91], "y":[4.63, 4.77, 4.91], "z":[4.63, 4.77, 4.91]}, "Q": {"x":[18, 20, 22], "y":[18, 20, 22], "z":[18, 20, 22]}},
    }
}

class LCRApp(QWidget):
    back_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ser = None
        self.last_selected_row = 0
        self.num_samples = 125 
        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('QC Measurement - L-Q Setup')
        self.resize(1100, 850)
        layout = QVBoxLayout()

        # Cấu hình phía trên
        top_layout = QHBoxLayout()
        self.combo_ports = QComboBox()
        self.btn_connect = QPushButton('Kết nối COM')
        self.btn_connect.clicked.connect(self.toggle_connection)
        top_layout.addWidget(QLabel('Cổng:'))
        top_layout.addWidget(self.combo_ports)
        top_layout.addWidget(self.btn_connect)
        layout.addLayout(top_layout)

        config_layout = QHBoxLayout()
        self.combo_line = QComboBox()
        self.combo_line.addItems(SPECS_DATA.keys())
        self.combo_line.currentTextChanged.connect(self.update_part_numbers)
        self.combo_part = QComboBox()
        self.update_part_numbers()
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 1000); self.spin_count.setValue(125)
        self.btn_set_table = QPushButton("XUẤT BẢNG")
        self.btn_set_table.clicked.connect(self.setup_table_rows)

        config_layout.addWidget(QLabel('Line:'))
        config_layout.addWidget(self.combo_line)
        config_layout.addWidget(QLabel('Mã PART:'))
        config_layout.addWidget(self.combo_part)
        config_layout.addWidget(QLabel('Số LK:'))
        config_layout.addWidget(self.spin_count)
        config_layout.addWidget(self.btn_set_table)
        layout.addLayout(config_layout)

        # --- DÒNG LOG TRẠNG THÁI (ĐÃ TRANG TRÍ) ---
        self.lbl_status = QLabel('CHỜ LỆNH ĐO...')
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFont(QFont('Arial', 22, QFont.Bold))
        self.lbl_status.setStyleSheet("color: red; padding: 15px; background-color: #FFFF00; border: 2px solid red; border-radius: 10px;")
        layout.addWidget(self.lbl_status)

        self.table = QTableWidget(125, 8)
        self.table.verticalHeader().setVisible(False) 
        headers = ['STT', 'Lx (mH)', 'Qx', 'Ly (mH)', 'Qy', 'Lz (mH)', 'Qz', 'STATUS LQ']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setup_table_rows() 
        self.table.itemClicked.connect(self.update_last_row)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton('← BACK')
        self.btn_back.setFixedHeight(50); self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setStyleSheet("background-color: #757575; color: white; font-weight: bold;")

        self.btn_run = QPushButton('BẮT ĐẦU ĐO L-Q')
        self.btn_run.setFixedHeight(50); self.btn_run.clicked.connect(self.auto_measure_process)
        self.btn_run.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        self.btn_export = QPushButton('XUẤT FILE CSV')
        self.btn_export.setFixedHeight(50); self.btn_export.clicked.connect(self.export_csv)
        self.btn_export.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        btn_layout.addWidget(self.btn_back); btn_layout.addWidget(self.btn_run); btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def setup_table_rows(self):
        self.num_samples = self.spin_count.value()
        self.table.setRowCount(self.num_samples)
        for i in range(self.num_samples):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        self.lbl_status.setText(f"ĐÃ TẠO BẢNG: {self.num_samples} LINH KIỆN")

    def update_last_row(self, item): self.last_selected_row = item.row()
    def update_part_numbers(self):
        line = self.combo_line.currentText()
        self.combo_part.clear()
        if line in SPECS_DATA: self.combo_part.addItems(SPECS_DATA[line].keys())
    def get_current_specs(self):
        line = self.combo_line.currentText()
        part = self.combo_part.currentText()
        return SPECS_DATA.get(line, {}).get(part, None)

    def evaluate_logic(self, val, spec_range):
        try:
            v = float(val)
            if isinstance(spec_range, (int, float)): # Dạng 1
                return ("PASS", QColor(200, 255, 200)) if v >= spec_range else ("FAIL", QColor(255, 150, 150))
            elif isinstance(spec_range, list) and len(spec_range) == 3: # Dạng 2
                low, center, high = spec_range
                if v < low or v > high: return "FAIL", QColor(255, 50, 50)
                margin = (high - low) * 0.02
                if v < (low + margin) or v > (high - margin): return "WARNING", QColor(255, 255, 150)
                return "PASS", QColor(150, 255, 150)
            return "ERROR", QColor(255, 255, 255)
        except: return "ERROR", QColor(255, 255, 255)

    def auto_measure_process(self):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối COM!"); return
        specs = self.get_current_specs()
        if not specs: return
        try:
            self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
            time.sleep(0.1)
            for row in range(self.last_selected_row, self.num_samples):
                self.table.selectRow(row); self.last_selected_row = row
                row_evals = []
                for i, axis in enumerate(['x', 'y', 'z']):
                    valid = False
                    while not valid:
                        self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: HÃY CHÂM KIM ĐO!")
                        QApplication.processEvents()
                        self.ser.reset_input_buffer()
                        self.ser.write(b":MEAS:TRIGger\n")
                        time.sleep(0.08); res = self.ser.readline().decode('ascii').strip()
                        if ',' in res:
                            try:
                                parts = res.split(',')
                                val_l = float(parts[0]); val_q = float(parts[1])
                                if 0 < val_l < 0.5 and val_q > 0.1:
                                    val_mh = val_l * 1000 
                                    l_st, l_color = self.evaluate_logic(val_mh, specs["L"][axis])
                                    q_st, q_color = self.evaluate_logic(val_q, specs["Q"][axis])
                                    self.table.setItem(row, 1 + i*2, QTableWidgetItem(f"{val_mh:.4f}"))
                                    self.table.item(row, 1 + i*2).setBackground(l_color)
                                    self.table.setItem(row, 2 + i*2, QTableWidgetItem(f"{val_q:.2f}"))
                                    self.table.item(row, 2 + i*2).setBackground(q_color)
                                    row_evals.extend([l_st, q_st]); valid = True
                            except: continue
                    
                    released = False
                    while not released:
                        self.lbl_status.setText(f"OK! NHẤC KIM TRỤC {axis.upper()} RA!")
                        QApplication.processEvents()
                        self.ser.reset_input_buffer()
                        self.ser.write(b":MEAS:TRIGger\n")
                        time.sleep(0.05); res_rel = self.ser.readline().decode('ascii').strip()
                        try:
                            if ',' in res_rel:
                                v = float(res_rel.split(',')[0])
                                if v > 0.5 or v <= 0: released = True
                            else: released = True
                        except: released = True
                
                if row_evals:
                    final_s = "PASS"; bg = QColor(150, 255, 150)
                    if "FAIL" in row_evals: final_s = "FAIL"; bg = QColor(255, 150, 150)
                    elif "WARNING" in row_evals: final_s = "WARNING"; bg = QColor(255, 255, 180)
                    item = QTableWidgetItem(final_s); item.setBackground(bg)
                    self.table.setItem(row, 7, item)
            self.lbl_status.setText("HOÀN TẤT ĐO!")
        except Exception as e: self.lbl_status.setText(f"LỖI: {str(e)}")

    def export_csv(self):
        if not os.path.exists(SAVE_FOLDER): os.makedirs(SAVE_FOLDER)
        now = datetime.now()
        filename = f"file1_LQ_{now.strftime('%d%m%Y_%H%M')}.csv"
        full_path = os.path.join(SAVE_FOLDER, filename)
        try:
            line = self.combo_line.currentText(); part = self.combo_part.currentText()
            with open(full_path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["LINE", line, "PART", part, "DATE", now.strftime("%d/%m/%Y %H:%M:%S")])
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(8)]
                writer.writerow(headers)
                for r in range(self.num_samples):
                    row_data = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(8)]
                    if row_data[1] != "": writer.writerow(row_data)
            QMessageBox.information(self, "Thành công", f"Đã lưu: {filename}")
        except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def go_back(self):
        if self.ser and self.ser.is_open:
            try: self.ser.write(b":SYSTem:LOCal\n"); time.sleep(0.1); self.ser.close()
            except: pass
        self.back_signal.emit(); self.close()

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
                self.btn_connect.setText("Ngắt kết nối")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else:
            try: self.ser.write(b":SYSTem:LOCal\n"); time.sleep(0.1); self.ser.close()
            except: pass
            self.ser = None; self.btn_connect.setText("Kết nối COM")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LCRApp(); ex.show(); sys.exit(app.exec_())