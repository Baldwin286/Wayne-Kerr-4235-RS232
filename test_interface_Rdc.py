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
# from PyQt5.QtGui import QColor, QFont

# # --- DỮ LIỆU SPECS ---
# SPECS_DATA = {
#     "3DC11-4": {
#         "X-10014-003": {"R": {"x":[72, 80, 88], "y":[81.45, 90.5, 99.55], "z":[149.4, 166, 182.6]}},
#         "X-10014-003R1": {"R": {"x":[72, 80, 88], "y":[81.45, 90.5, 99.55], "z":[149.4, 166, 182.6]}},
#         "X-D0287-044R2": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
#         "X-D0287-087": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121, 135, 149]}},
#         "X-13830-001": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
#         "3DC11LP-0720J": {"R": {"x":[135, 150, 155], "y":[144, 160, 176], "z":[181, 190, 199]}},
#         "X-10101-058R1": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
#         "X-14613-002": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
#         "X-13942-002": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
#         "X-12702-008": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
#         "X-14012-001": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
#         "X-W0113-068": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
#         "3DC11LPS-0470J": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
#         "3DC11LP-0477J": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
#         "3DC11LPS-LC-0470": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
#         "X-14228-003": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
#         "X-12190-001": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
#     }
# }

# class RdcApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.ser = None
#         self.last_selected_row = 0
#         self.initUI()
#         self.refresh_ports()

#     def initUI(self):
#         self.setWindowTitle('QC Measurement - Rdc Intelligent Filter')
#         self.resize(1000, 800)
#         layout = QVBoxLayout()

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

#         self.table = QTableWidget(125, 5)
#         self.table.verticalHeader().setVisible(False) 
#         headers = ['STT', 'Rx (Ω)', 'Ry (Ω)', 'Rz (Ω)', 'STATUS']
#         self.table.setHorizontalHeaderLabels(headers)
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#         for i in range(125):
#             self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
#         self.table.itemClicked.connect(self.update_last_row)
#         layout.addWidget(self.table)

#         btn_layout = QHBoxLayout()
#         self.btn_run = QPushButton('BẮT ĐẦU ĐO R (DỰA VÀO SPECS)')
#         self.btn_run.setFixedHeight(50)
#         self.btn_run.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold;")
#         self.btn_run.clicked.connect(self.auto_measure_process)
        
#         self.btn_export = QPushButton('XUẤT FILE CSV')
#         self.btn_export.setFixedHeight(50)
#         self.btn_export.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
#         self.btn_export.clicked.connect(self.export_csv)

#         btn_layout.addWidget(self.btn_run)
#         btn_layout.addWidget(self.btn_export)
#         layout.addLayout(btn_layout)

#         self.lbl_status = QLabel('Trạng thái: Sẵn sàng.')
#         layout.addWidget(self.lbl_status)
#         self.setLayout(layout)

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

#     def extract_number(self, text):
#         try:
#             match = re.search(r"[-+]?\d*\.\d+|\d+", text)
#             return float(match.group()) if match else None
#         except: return None

#     def evaluate_logic(self, val, spec_range):
#         v = float(val)
#         low, center, high = spec_range
#         if v < low or v > high: return "FAIL", QColor(255, 50, 50)
#         margin = (high - low) * 0.02
#         if v < (low + margin) or v > (high - margin): return "WARNING", QColor(255, 255, 150)
#         return "PASS", QColor(150, 255, 150)

#     def auto_measure_process(self):
#         if not self.ser or not self.ser.is_open:
#             QMessageBox.warning(self, "Lỗi", "Hãy kết nối cổng COM!")
#             return
        
#         specs = self.get_current_specs()
#         if not specs: return

#         try:
#             self.ser.write(b":MEAS:FUNC1 Rdc\n")
#             time.sleep(0.2)

#             for row in range(self.last_selected_row, 125):
#                 self.table.selectRow(row)
#                 self.last_selected_row = row
#                 row_evals = []
#                 axes = ['x', 'y', 'z']

#                 for i, axis in enumerate(axes):
#                     # --- THIẾT LẬP BỘ LỌC DỰA VÀO SPECS ---
#                     axis_spec = specs["R"][axis]
#                     filter_low = axis_spec[0] * 0.5  # Chấp nhận thấp nhất 50% so với Spec Min
#                     filter_high = axis_spec[2] * 2.0 # Chấp nhận cao nhất 200% so với Spec Max

#                     valid = False
#                     while not valid:
#                         self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: CHỜ KIM (Lọc: {filter_low:.0f}-{filter_high:.0f} Ω)")
#                         self.lbl_status.setStyleSheet("color: blue; font-weight: bold;")
#                         QApplication.processEvents()
                        
#                         self.ser.reset_input_buffer() 
#                         self.ser.write(b":MEAS:TRIGger;:MEAS:ALL?\n") 
#                         time.sleep(0.2) 
#                         res = self.ser.readline().decode('ascii').strip()
#                         val_r = self.extract_number(res)
                        
#                         # --- KIỂM TRA GIÁ TRỊ VỚI BỘ LỌC SPECS ---
#                         if val_r is not None and filter_low < val_r < filter_high:
#                             st, color = self.evaluate_logic(val_r, axis_spec)
#                             it_r = QTableWidgetItem(f"{val_r:.2f}")
#                             it_r.setBackground(color)
#                             self.table.setItem(row, 1 + i, it_r)
#                             row_evals.append(st)
#                             valid = True
#                         else:
#                             time.sleep(0.05) # Giá trị rác hoặc hở mạch -> Bỏ qua

#                     # Chờ rút kim (Dựa vào việc giá trị nhảy ra ngoài dải lọc)
#                     released = False
#                     while not released:
#                         self.lbl_status.setText(f"OK! HÃY NHẤC KIM {axis.upper()}")
#                         self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
#                         QApplication.processEvents()
#                         self.ser.write(b":MEAS:ALL?\n")
#                         time.sleep(0.05)
#                         v_chk = self.extract_number(self.ser.readline().decode('ascii').strip())
#                         if v_chk is None or v_chk > filter_high or v_chk < filter_low:
#                             released = True

#                 if row_evals:
#                     final_s = "PASS"; bg = QColor(150, 255, 150)
#                     if "FAIL" in row_evals: final_s = "FAIL"; bg = QColor(255, 150, 150)
#                     elif "WARNING" in row_evals: final_s = "WARNING"; bg = QColor(255, 255, 180)
#                     s_item = QTableWidgetItem(final_s); s_item.setBackground(bg)
#                     self.table.setItem(row, 4, s_item)

#             QMessageBox.information(self, "Xong", "Hoàn tất đo Rdc.")
#         except Exception as e: self.lbl_status.setText(f"Lỗi: {str(e)}")

#     def export_csv(self):
#         line = self.combo_line.currentText()
#         part = self.combo_part.currentText()
#         date_str = datetime.now().strftime("%d%m%Y")
#         # Tên file đúng yêu cầu: Line_Part_NgayThangNam_Rdc.csv
#         filename = f"{line}_{part}_{date_str}_Rdc.csv"
        
#         path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV", filename, "CSV Files (*.csv)")
#         if path:
#             try:
#                 with open(path, 'w', newline='', encoding='utf-8-sig') as f:
#                     writer = csv.writer(f)
#                     writer.writerow(["LINE", line, "PART", part, "DATE", date_str])
#                     headers = [self.table.horizontalHeaderItem(i).text() for i in range(5)]
#                     writer.writerow(headers)
#                     for r in range(125):
#                         row_data = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(5)]
#                         if any(row_data[1:]): writer.writerow(row_data)
#                 QMessageBox.information(self, "Xong", f"Đã lưu: {path}")
#             except: pass

#     def toggle_connection(self):
#         if self.ser is None:
#             try:
#                 self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
#                 self.btn_connect.setText("Ngắt kết nối")
#             except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
#         else:
#             try:
#                 self.ser.write(b":SYSTem:LOCal\n")
#                 time.sleep(0.1); self.ser.close()
#             except: pass
#             self.ser = None
#             self.btn_connect.setText("Kết nối COM")

#     def refresh_ports(self):
#         self.combo_ports.clear()
#         for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = RdcApp(); ex.show()
#     sys.exit(app.exec_())

import sys
import serial
import serial.tools.list_ports
import time
import csv
import re
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog, QSpinBox)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import pyqtSignal, Qt

# --- ĐƯỜNG DẪN THƯ MỤC LƯU FILE ---
SAVE_FOLDER = r"F:\TTTN\auto_measure_LCR\CSV_data\3DC_30022026" 

# --- DỮ LIỆU SPECS ĐẦY ĐỦ ---
SPECS_DATA = {
    "3DC11-4": {
        "X-10014-003": {"R": {"x":[72, 80, 88], "y":[81.45, 90.5, 99.55], "z":[149.4, 166, 182.6]}},
        "X-10014-003R1": {"R": {"x":[72, 80, 88], "y":[81.45, 90.5, 99.55], "z":[149.4, 166, 182.6]}},
        "X-D0287-044R2": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "X-D0287-087": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121, 135, 149]}},
        "X-13830-001": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "3DC11LP-0720J": {"R": {"x":[135, 150, 155], "y":[144, 160, 176], "z":[181, 190, 199]}},
        "X-10101-058R1": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-14613-002": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-13942-002": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-12702-008": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-14012-001": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "X-W0113-068": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
        "3DC11LPS-0470J": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
        "3DC11LP-0477J": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "3DC11LPS-LC-0470": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[171, 190, 209]}},
        "X-14228-003": {"R": {"x":[135, 150, 165], "y":[144, 160, 176], "z":[189, 210, 231]}},
        "X-12190-001": {"R": {"x":[81, 90, 99], "y":[90, 100, 110], "z":[121.5, 135, 148.5]}},
        "3DC09LP-0720J": {"R": {"x":[171, 180, 209], "y":[180, 200, 220], "z":[148.5, 165, 181.5]}},
    }
}

class RdcApp(QWidget):
    back_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ser = None
        self.last_selected_row = 0
        self.num_samples = 125
        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('QC Measurement - Rdc Setup')
        self.resize(1000, 850)
        layout = QVBoxLayout()

        # Dòng 1: Kết nối COM
        top_layout = QHBoxLayout()
        self.combo_ports = QComboBox()
        self.btn_connect = QPushButton('Kết nối COM')
        self.btn_connect.clicked.connect(self.toggle_connection)
        top_layout.addWidget(QLabel('Cổng:'))
        top_layout.addWidget(self.combo_ports)
        top_layout.addWidget(self.btn_connect)
        layout.addLayout(top_layout)

        # Dòng 2: Cấu hình
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

        # --- DÒNG LOG TRẠNG THÁI (TRANG TRÍ) ---
        self.lbl_status = QLabel('CHỜ LỆNH ĐO R...')
        self.lbl_status.setAlignment(Qt.AlignCenter) # VÀO GIỮA
        self.lbl_status.setFont(QFont('Arial', 22, QFont.Bold)) # CHỮ TO, ĐẬM
        self.lbl_status.setStyleSheet("color: red; padding: 15px; background-color: #FFFF00; border: 2px solid red; border-radius: 10px;")
        layout.addWidget(self.lbl_status)

        # Bảng dữ liệu
        self.table = QTableWidget(125, 5)
        self.table.verticalHeader().setVisible(False) 
        headers = ['STT', 'Rx (Ω)', 'Ry (Ω)', 'Rz (Ω)', 'STATUS Rdc']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setup_table_rows()
        self.table.itemClicked.connect(self.update_last_row)
        layout.addWidget(self.table)

        # Nút điều khiển
        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton('← BACK')
        self.btn_back.setFixedHeight(50); self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setStyleSheet("background-color: #757575; color: white; font-weight: bold;")

        self.btn_run = QPushButton('BẮT ĐẦU ĐO R')
        self.btn_run.setFixedHeight(50); self.btn_run.clicked.connect(self.auto_measure_process)
        self.btn_run.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold;")
        
        self.btn_export = QPushButton('XUẤT FILE CSV')
        self.btn_export.setFixedHeight(50); self.btn_export.clicked.connect(self.export_csv)
        self.btn_export.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")

        btn_layout.addWidget(self.btn_back); btn_layout.addWidget(self.btn_run); btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def setup_table_rows(self):
        self.num_samples = self.spin_count.value()
        self.table.setRowCount(self.num_samples)
        for i in range(self.num_samples):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
        self.lbl_status.setText(f"ĐÃ TẠO BẢNG CHO {self.num_samples} LINH KIỆN.")

    def update_last_row(self, item): self.last_selected_row = item.row()
    def update_part_numbers(self):
        line = self.combo_line.currentText(); self.combo_part.clear()
        if line in SPECS_DATA: self.combo_part.addItems(SPECS_DATA[line].keys())
    def get_current_specs(self):
        line = self.combo_line.currentText(); part = self.combo_part.currentText()
        return SPECS_DATA.get(line, {}).get(part, None)
    def extract_number(self, text):
        try:
            match = re.search(r"[-+]?\d*\.\d+|\d+", text)
            return float(match.group()) if match else None
        except: return None

    def evaluate_logic(self, val, spec_range):
        v = float(val); low, center, high = spec_range
        if v < low or v > high: return "FAIL", QColor(255, 50, 50)
        margin = (high - low) * 0.02
        if v < (low + margin) or v > (high - margin): return "WARNING", QColor(255, 255, 150)
        return "PASS", QColor(150, 255, 150)

    def auto_measure_process(self):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Lỗi", "Hãy kết nối cổng COM!"); return
        specs = self.get_current_specs()
        if not specs: return
        try:
            self.ser.write(b":MEAS:FUNC1 Rdc\n"); time.sleep(0.2)
            for row in range(self.last_selected_row, self.num_samples):
                self.table.selectRow(row); self.last_selected_row = row
                row_evals = []
                for i, axis in enumerate(['x', 'y', 'z']):
                    axis_spec = specs["R"][axis]
                    filter_low, filter_high = axis_spec[0] * 0.5, axis_spec[2] * 2.0
                    
                    valid = False
                    while not valid:
                        self.lbl_status.setText(f"LK {row+1}-{axis.upper()}: HÃY CHÂM KIM ĐO R!")
                        QApplication.processEvents()
                        self.ser.reset_input_buffer() 
                        self.ser.write(b":MEAS:TRIGger;:MEAS:ALL?\n") 
                        time.sleep(0.2); res = self.ser.readline().decode('ascii').strip()
                        val_r = self.extract_number(res)
                        if val_r is not None and filter_low < val_r < filter_high:
                            st, color = self.evaluate_logic(val_r, axis_spec)
                            it = QTableWidgetItem(f"{val_r:.2f}"); it.setBackground(color)
                            self.table.setItem(row, 1 + i, it); row_evals.append(st); valid = True
                        else: time.sleep(0.05)

                    released = False
                    while not released:
                        self.lbl_status.setText(f"OK! NHẤC KIM TRỤC {axis.upper()} RA!")
                        QApplication.processEvents()
                        self.ser.reset_input_buffer()
                        self.ser.write(b":MEAS:TRIGger;:MEAS:ALL?\n")
                        time.sleep(0.1); res_rel = self.ser.readline().decode('ascii').strip()
                        v_chk = self.extract_number(res_rel)
                        if v_chk is None or v_chk > filter_high or v_chk < filter_low: released = True
                        else: time.sleep(0.05)
                    self.ser.reset_input_buffer(); time.sleep(0.1)

                if len(row_evals) >= 3:
                    final_s = "PASS"; bg = QColor(150, 255, 150)
                    if "FAIL" in row_evals: final_s = "FAIL"; bg = QColor(255, 150, 150)
                    elif "WARNING" in row_evals: final_s = "WARNING"; bg = QColor(255, 255, 180)
                    self.table.setItem(row, 4, QTableWidgetItem(final_s))
                    self.table.item(row, 4).setBackground(bg)
            self.lbl_status.setText("HOÀN TẤT QUÁ TRÌNH ĐO Rdc!")
        except Exception as e: self.lbl_status.setText(f"LỖI: {str(e)}")

    def export_csv(self):
        if not os.path.exists(SAVE_FOLDER): os.makedirs(SAVE_FOLDER)
        now = datetime.now()
        filename = f"file2_Rdc_{now.strftime('%d%m%Y_%H%M')}.csv"
        full_path = os.path.join(SAVE_FOLDER, filename)
        try:
            line = self.combo_line.currentText(); part = self.combo_part.currentText()
            with open(full_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["LINE", line, "PART", part, "TYPE", "Rdc", "DATE", now.strftime("%d/%m/%Y %H:%M:%S")])
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(5)]
                writer.writerow(headers)
                for r in range(self.num_samples):
                    row_data = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(5)]
                    if any(row_data[1:]): writer.writerow(row_data)
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
    app = QApplication(sys.argv); ex = RdcApp(); ex.show(); sys.exit(app.exec_())