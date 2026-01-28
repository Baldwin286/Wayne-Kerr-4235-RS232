import sys
import serial
import serial.tools.list_ports
import time
import csv
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog,
                             QFrame, QGroupBox, QLineEdit, QFormLayout)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- LỚP TỰ XÓA 0 ---
class AutoClearLineEdit(QLineEdit):
    def focusInEvent(self, event):
        if self.text() == "0":
            self.clear()
        super().focusInEvent(event)

# --- LUỒNG ĐO RIÊNG (CHỐNG LAG & CẬP NHẬT CHẬM) ---
class MeasureWorker(QThread):
    data_signal = pyqtSignal(int, int, float, float, QColor, str)
    row_signal = pyqtSignal(int, str, QColor)
    msg_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, ser, specs, total_qty, mode="LQ"):
        super().__init__()
        self.ser = ser
        self.specs = specs
        self.total_qty = total_qty
        self.mode = mode
        self.is_running = True

    def run(self):
        try:
            if self.mode == "LQ": self.measure_lq()
            else: self.measure_r()
        except Exception as e:
            self.error_signal.emit(f"Mất kết nối: {str(e)}")

# --- LOGIC SO SÁNH ---
    def evaluate(self, val, s_min, s_center, s_max, q_val, q_limit):
        if val < s_min or val > s_max or q_val < q_limit:
            return "FAIL", QColor(244, 67, 54)
        warn_zone = (s_max - s_min) * 0.15
        if (val <= s_min + warn_zone) or (val >= s_max - warn_zone):
            return "WARNING", QColor(255, 235, 59)
        return "PASS", QColor(76, 175, 80)

    def measure_lq(self):
        self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
        for row in range(self.total_qty):
            if not self.is_running: break
            row_evals = []
            for pair_idx, axis in zip([1, 3, 5], ['LX', 'LY', 'LZ']):
                s_min, s_max = self.specs[f"{axis}_MIN"], self.specs[f"{axis}_MAX"]
                s_center = self.specs[f"{axis}_CENTER"] if f"{axis}_CENTER" in self.specs else (s_min+s_max)/2
                q_col = f"Q{axis[-1]}_MIN" if f"Q{axis[-1]}_MIN" in self.specs else f"Q_{axis[-1]}_MIN"
                q_limit = self.specs[q_col]
                
                self.msg_signal.emit(f"LK {row+1}: ĐANG ĐO {axis}...")
                stable_count, last_l = 0, 0
                while self.is_running:
                    self.ser.write(b":MEAS:TRIGger\n")
                    line = self.ser.readline().decode('ascii').strip()
                    try:
                        if ',' in line:
                            parts = line.split(',')
                            l_val = float(parts[0]) * 1000; q_val = float(parts[1])
                            if s_min * 0.7 <= l_val <= s_max * 1.3:
                                if abs(l_val - last_l) < (s_max - s_min) * 0.01: stable_count += 1
                                else: stable_count = 0
                                last_l = l_val
                                if stable_count >= 2:
                                    st, color = self.evaluate(l_val, s_min, s_center, s_max, q_val, q_limit)
                                    self.data_signal.emit(row, pair_idx, l_val, q_val, color, st)
                                    row_evals.append(st); break
                    except: pass
                    time.sleep(0.05)
                self.msg_signal.emit(f"LK {row+1}: NHẤC KIM {axis} OK.")
                while self.is_running:
                    self.ser.write(b":MEAS:TRIGger\n")
                    line = self.ser.readline().decode('ascii').strip()
                    try:
                        if float(line.split(',')[0])*1000 < s_min * 0.5: break
                    except: break
            
            final = "FAIL" if "FAIL" in row_evals else ("WARNING" if "WARNING" in row_evals else "PASS")
            color_st = QColor(76,175,80) if final=="PASS" else (QColor(244,67,54) if final=="FAIL" else QColor(255,235,59))
            self.row_signal.emit(row, final, color_st)

    def measure_r(self):
        self.ser.write(b":MEAS:FUNC1 R\n:MEAS:FUNC2 NONE\n")
        r_cols = [('RX_MIN', 'RX_CENTER', 'RX_MAX'), ('RY_MIN', 'RY_CENTER', 'RY_MAX'), ('RZ_MIN', 'RZ_CENTER', 'RZ_MAX')]
        for row in range(self.total_qty):
            for i, (cmin, ccenter, cmax) in enumerate(r_cols):
                s_min, s_center, s_max = self.specs[cmin], self.specs[ccenter], self.specs[cmax]
                self.msg_signal.emit(f"LK {row+1}: ĐO {['RX','RY','RZ'][i]}...")
                while self.is_running:
                    self.ser.write(b":MEAS:TRIGger\n")
                    line = self.ser.readline().decode('ascii').strip()
                    try:
                        r = float(line.split(',')[0])
                        if r < s_max * 1.5:
                            st, color = self.evaluate(r, s_min, s_center, s_max, 100, 1)
                            self.data_signal.emit(row, 7 + i, r, 0, color, st)
                            break
                    except: pass
            time.sleep(0.3)

class MplsChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111)
        super(MplsChart, self).__init__(self.fig)

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.df_database = pd.DataFrame()
        self.load_database()
        self.initUI()
        self.refresh_ports()

    def load_database(self):
        try:
            self.df_database = pd.read_excel(r'F:\TTTN\auto_measure_LCR\data_test.xlsx')
            self.df_database['Line'] = self.df_database['Line'].ffill()
            self.df_database.columns = self.df_database.columns.str.strip().str.upper()
        except: pass

    def initUI(self):
        self.setWindowTitle('Hệ thống QC LCR - Wayne Kerr 4235')
        self.resize(1600, 950)
        self.setStyleSheet("background-color: #f5f5f5;")
        main_layout = QHBoxLayout(self)

        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)

        config_group = QGroupBox("Điều Khiển Hệ Thống")
        config_group.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 20px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; background-color: #f5f5f5; }
        """)
        config_layout = QVBoxLayout(config_group)

        com_layout = QHBoxLayout()
        com_layout.addWidget(QLabel("Cổng COM:"))
        self.combo_ports = QComboBox()
        self.btn_connect = QPushButton("KẾT NỐI")
        self.btn_connect.setFixedWidth(100)
        self.btn_connect.clicked.connect(self.toggle_connection)
        com_layout.addWidget(self.combo_ports, 1)
        com_layout.addWidget(self.btn_connect)
        config_layout.addLayout(com_layout)

        form_layout = QFormLayout()
        self.cb_line = QComboBox()
        if not self.df_database.empty:
            self.cb_line.addItems(sorted(self.df_database['LINE'].unique().astype(str)))
        self.cb_line.currentTextChanged.connect(self.update_pns)
        
        self.cb_pn = QComboBox()
        self.txt_qty = AutoClearLineEdit()
        self.txt_qty.setText("0")
        
        form_layout.addRow("Line sản xuất:", self.cb_line)
        form_layout.addRow("Mã linh kiện (PN):", self.cb_pn)
        form_layout.addRow("Số lượng (Qty):", self.txt_qty)
        config_layout.addLayout(form_layout)

        self.btn_setup = QPushButton("KHỞI TẠO BẢNG SẢN XUẤT")
        self.btn_setup.setFixedHeight(40); self.btn_setup.setStyleSheet("background-color: #455a64; color: white; font-weight: bold;")
        self.btn_setup.clicked.connect(self.setup_table)
        config_layout.addWidget(self.btn_setup)
        left_layout.addWidget(config_group)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        left_layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        self.btn_lq = QPushButton('BẮT ĐẦU ĐO L-Q')
        self.btn_lq.setFixedHeight(60); self.btn_lq.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold; font-size: 12pt;")
        self.btn_lq.clicked.connect(lambda: self.start_measure("LQ"))
        self.btn_r = QPushButton('BẮT ĐẦU ĐO R')
        self.btn_r.setFixedHeight(60); self.btn_r.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; font-size: 12pt;")
        self.btn_r.clicked.connect(lambda: self.start_measure("R"))
        btn_box.addWidget(self.btn_lq); btn_box.addWidget(self.btn_r)
        left_layout.addLayout(btn_box)

        self.lbl_msg = QLabel("HỆ THỐNG SẴN SÀNG")
        self.lbl_msg.setAlignment(Qt.AlignCenter); self.lbl_msg.setStyleSheet("color: red; font-weight: bold; font-size: 30pt; padding: 10px;")
        left_layout.addWidget(self.lbl_msg)

        self.btn_export = QPushButton('XUẤT BÁO CÁO CSV')
        self.btn_export.setFixedHeight(45); self.btn_export.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold;")
        left_layout.addWidget(self.btn_export)

        right_container = QGroupBox("Phân Tích Chất Lượng")
        right_container.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 12px; background-color: white; margin-top: 20px; padding-top: 30px; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 10px; background-color: white; }
        """)
        right_layout = QVBoxLayout(right_container)
        self.lbl_chart_title = QLabel("TỶ LỆ %"); self.lbl_chart_title.setAlignment(Qt.AlignCenter)
        self.lbl_chart_title.setStyleSheet("font-size: 22pt; font-weight: bold;")
        right_layout.addWidget(self.lbl_chart_title)

        self.chart = MplsChart(self); right_layout.addWidget(self.chart, 5)

        self.lbl_pass = QLabel("PASS: 0 (0.0%)"); self.lbl_fail = QLabel("FAIL: 0 (0.0%)"); self.lbl_warn = QLabel("WARNING: 0 (0.0%)")
        for i, lbl in enumerate([self.lbl_pass, self.lbl_fail, self.lbl_warn]):
            color = ['#4CAF50', '#F44336', '#FFEB3B'][i]
            lbl.setFixedHeight(50); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"background-color: {color}; color: {'white' if i<2 else 'black'}; font-weight: bold; font-size: 15pt; border-radius: 10px; margin-bottom: 5px;")
            right_layout.addWidget(lbl)
        
        main_layout.addWidget(left_container, 65); main_layout.addWidget(right_container, 35)
        self.update_pns(); self.update_chart()

    def update_pns(self):
        line = self.cb_line.currentText()
        self.cb_pn.clear()
        if not self.df_database.empty:
            parts = self.df_database[self.df_database['LINE'] == line]['PART NUMBER'].unique().astype(str)
            self.cb_pn.addItems(sorted(parts))

    def setup_table(self):
        try:
            qty = int(self.txt_qty.text())
            self.table.setRowCount(qty)
            for i in range(qty):
                it = QTableWidgetItem(str(i+1)); it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 0, it)
            self.lbl_msg.setText(f"ĐÃ KHỞI TẠO {qty} LINH KIỆN")
            self.update_chart()
        except: pass

    def start_measure(self, mode):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Cảnh báo", "Chưa kết nối máy đo!")
            return
        pn = self.cb_pn.currentText()
        specs = self.df_database[self.df_database['PART NUMBER'] == pn].iloc[0]
        self.worker = MeasureWorker(self.ser, specs, self.table.rowCount(), mode)
        self.worker.data_signal.connect(self.on_data_received)
        self.worker.row_signal.connect(self.on_row_finished)
        self.worker.msg_signal.connect(self.lbl_msg.setText)
        self.worker.error_signal.connect(lambda err: QMessageBox.critical(self, "Lỗi", err))
        self.worker.start()

    def on_data_received(self, row, col, v1, v2, color, st):
        it1 = QTableWidgetItem(f"{v1:.3f}"); it1.setBackground(color); it1.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, it1)
        if col in [1, 3, 5]:
            it2 = QTableWidgetItem(f"{v2:.2f}"); it2.setBackground(color); it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col + 1, it2)
        self.table.scrollToItem(it1)

    def on_row_finished(self, row, status, color):
        it = QTableWidgetItem(status); it.setBackground(color); it.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 10, it)
        self.update_chart()

    def update_chart(self):
        p, f, w = 0, 0, 0
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 10)
            if it:
                if it.text() == "PASS": p += 1
                elif it.text() == "FAIL": f += 1
                elif it.text() == "WARNING": w += 1
        total = (p + f + w) or 1
        self.chart.axes.clear()
        self.chart.axes.pie([p, f, w] if (p+f+w)>0 else [1], colors=['#4CAF50', '#F44336', '#FFEB3B'] if (p+f+w)>0 else ['#eee'], startangle=90, wedgeprops=dict(width=0.45))
        self.chart.draw()
        self.lbl_pass.setText(f"PASS: {p} ({(p/total)*100:.1f}%)")
        self.lbl_fail.setText(f"FAIL: {f} ({(f/total)*100:.1f}%)")
        self.lbl_warn.setText(f"WARNING: {w} ({(w/total)*100:.1f}%)")

    # --- HÀM SỬA LỖI TREO KHI CHỌN CỔNG LỖI ---
    def toggle_connection(self):
        if self.ser is None:
            port = self.combo_ports.currentText()
            if not port: return
            try:
                # Tạo đối tượng Serial 
                test_ser = serial.Serial()
                test_ser.port = port
                test_ser.baudrate = 9600
                test_ser.timeout = 1.0       
                test_ser.write_timeout = 1.0 
                
                test_ser.open()
                
                test_ser.write(b"*IDN?\n")
                time.sleep(0.1)
                response = test_ser.readline().decode('ascii').strip()
                
                if response:
                    self.ser = test_ser
                    self.ser.timeout = 0.1 
                    self.btn_connect.setText("NGẮT")
                    self.btn_connect.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
                    self.lbl_msg.setText(f"ĐÃ KẾT NỐI: {response[:20]}...")
                else:
                    test_ser.close()
                    QMessageBox.critical(self, "Lỗi kết nối", "Không tìm thấy máy đo!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi kết nối", "Không tìm thấy máy đo!")
        else:
            self.ser.close()
            self.ser = None
            self.btn_connect.setText("KẾT NỐI")
            self.btn_connect.setStyleSheet("")
            self.lbl_msg.setText("ĐÃ NGẮT KẾT NỐI")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

    def export_csv(self): pass

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = LCRApp(); ex.show(); sys.exit(app.exec_())