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
                             QFrame, QGroupBox, QLineEdit, QFormLayout, QTextEdit)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AutoClearLineEdit(QLineEdit):
    def focusInEvent(self, event):
        if self.text() == "0":
            self.clear()
        super().focusInEvent(event)

# ================== LUỒNG ĐO THỰC TẾ ==================
class MeasureWorker(QThread):
    data_signal = pyqtSignal(int, int, float, float, QColor, str)
    row_signal = pyqtSignal(int, str, QColor)
    msg_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    raw_signal = pyqtSignal(str)

    def __init__(self, ser, specs, total_qty, mode="LQ"):
        super().__init__()
        self.ser, self.specs, self.total_qty, self.mode = ser, specs, total_qty, mode
        self.is_running = True

    def run(self):
        try:
            if self.mode == "LQ": self.measure_lq()
            else: self.measure_r()
        except Exception as e:
            self.error_signal.emit(f"LỖI TRONG KHI ĐO: {str(e)}")

    def evaluate(self, val, s_min, s_center, s_max, q_val, q_limit):
        if val < s_min or val > s_max or q_val < q_limit:
            return "FAIL", QColor(244, 67, 54)
        band = s_max - s_min
        warn_zone = band * 0.15 
        if (val <= s_min + warn_zone) or (val >= s_max - warn_zone):
            return "WARNING", QColor(255, 235, 59)
        return "PASS", QColor(76, 175, 80)

    def measure_lq(self):
        self.ser.write(b":MEASure:FUNC1 L\r\n:MEASure:FUNC2 Q\r\n")
        for row in range(self.total_qty):
            if not self.is_running: break
            row_evals = []
            for pair_idx, axis in zip([1, 3, 5], ['LX', 'LY', 'LZ']):
                s_min = float(self.specs[f"{axis}_MIN"])
                s_max = float(self.specs[f"{axis}_MAX"])
                s_center = float(self.specs[f"{axis}_CENTER"])
                q_limit = float(self.specs.get(f"Q{axis[-1]}_MIN", self.specs.get(f"Q_{axis[-1]}_MIN", 0)))
                
                self.msg_signal.emit(f"LK {row+1}: ĐANG ĐO {axis}...")
                stb, last_val = 0, 0
                while self.is_running:
                    self.ser.write(b":MEASure:TRIGger\r\n")
                    time.sleep(0.15)
                    self.ser.write(b":MEASure:RESult?\r\n")
                    line = self.ser.readline().decode('ascii').strip()
                    if line: self.raw_signal.emit(line)
                    if ',' in line:
                        try:
                            parts = line.split(',')
                            v_l_mh = float(parts[0]) * 1000 
                            v_q = float(parts[1])
                            if (s_min * 0.5) <= v_l_mh <= (s_max * 1.5):
                                if abs(v_l_mh - last_val) < (s_max - s_min) * 0.01: stb += 1
                                else: stb = 0
                                last_val = v_l_mh
                                if stb >= 2:
                                    st, clr = self.evaluate(v_l_mh, s_min, s_center, s_max, v_q, q_limit)
                                    self.data_signal.emit(row, pair_idx, v_l_mh, v_q, clr, st)
                                    row_evals.append(st); break
                        except: pass
                
                self.msg_signal.emit(f"LK {row+1}: NHẤC KIM OK.")
                while self.is_running:
                    self.ser.write(b":MEASure:RESult?\r\n")
                    res = self.ser.readline().decode('ascii').strip()
                    try:
                        if res and ',' in res:
                            v_c = float(res.split(',')[0]) * 1000
                            if v_c > s_max * 5 or v_c < s_min * 0.1: break
                    except: break
                    time.sleep(0.1)

            f_st = "FAIL" if "FAIL" in row_evals else ("WARNING" if "WARNING" in row_evals else "PASS")
            self.row_signal.emit(row, f_st, QColor(76,175,80) if f_st=="PASS" else (QColor(244,67,54) if f_st=="FAIL" else QColor(255,235,59)))

    def measure_r(self):
        self.ser.write(b":MEASure:FUNC1 R\r\n")
        r_cols = [('RX_MIN', 'RX_CENTER', 'RX_MAX'), ('RY_MIN', 'RY_CENTER', 'RY_MAX'), ('RZ_MIN', 'RZ_CENTER', 'RZ_MAX')]
        for row in range(self.total_qty):
            for i, (cmin, ccenter, cmax) in enumerate(r_cols):
                s_min, s_center, s_max = float(self.specs[cmin]), float(self.specs[ccenter]), float(self.specs[cmax])
                self.msg_signal.emit(f"LK {row+1}: ĐO {['RX','RY','RZ'][i]}...")
                while self.is_running:
                    self.ser.write(b":MEASure:TRIGger\r\n")
                    time.sleep(0.2); self.ser.write(b":MEASure:RESult?\r\n")
                    line = self.ser.readline().decode('ascii').strip()
                    if line: self.raw_signal.emit(line)
                    try:
                        if ',' in line:
                            r = float(line.split(',')[0])
                            if r < 1000000:
                                st, clr = self.evaluate(r, s_min, s_center, s_max, 999, 0)
                                self.data_signal.emit(row, 7 + i, r, 0, clr, st); break
                    except: pass

# --- BIỂU ĐỒ ---
class MplsChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111)
        super(MplsChart, self).__init__(self.fig)

# ================== GIAO DIỆN CHÍNH ==================
class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser, self.df_database = None, pd.DataFrame()
        self.load_database(); self.initUI(); self.refresh_ports()

    def load_database(self):
        try:
            self.df_database = pd.read_excel(r'F:\TTTN\auto_measure_LCR\data_test.xlsx')
            self.df_database['Line'] = self.df_database['Line'].ffill()
            self.df_database.columns = self.df_database.columns.str.strip().str.upper()
        except: pass

    def initUI(self):
        self.setWindowTitle('Hệ thống QC LCR - Wayne Kerr 4300 Series (Real-time)')
        self.resize(1600, 950); self.setStyleSheet("background-color: #f5f5f5;")
        main_layout = QHBoxLayout(self)

        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)

        cfg = QGroupBox("Điều Khiển Hệ Thống")
        cfg.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 15px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; background-color: #f5f5f5; }
        """)
        cfg_l = QFormLayout(cfg)
        
        # Cụm kết nối
        com_l = QHBoxLayout()
        self.cb_ports = QComboBox(); 
        self.btn_conn = QPushButton("KẾT NỐI")
        self.btn_disconn = QPushButton("NGẮT KẾT NỐI")
        self.btn_disconn.setEnabled(False) # Mặc định chưa có kết nối thì tắt nút ngắt
        
        self.btn_conn.clicked.connect(self.connect_device)
        self.btn_disconn.clicked.connect(self.disconnect_device)
        
        com_l.addWidget(QLabel("Cổng COM:")); com_l.addWidget(self.cb_ports, 1)
        com_l.addWidget(self.btn_conn); com_l.addWidget(self.btn_disconn)
        cfg_l.addRow(com_l)

        self.cb_line, self.cb_pn, self.txt_qty = QComboBox(), QComboBox(), AutoClearLineEdit()
        self.txt_qty.setText("0")
        if not self.df_database.empty: self.cb_line.addItems(sorted(self.df_database['LINE'].unique().astype(str)))
        self.cb_line.currentTextChanged.connect(self.update_pns)
        cfg_l.addRow("Line sản xuất:", self.cb_line); cfg_l.addRow("Mã linh kiện:", self.cb_pn); cfg_l.addRow("Số lượng đo:", self.txt_qty)
        
        btn_set = QPushButton("KHỞI TẠO BẢNG MỚI"); btn_set.setFixedHeight(40); btn_set.setStyleSheet("background-color: #455a64; color: white; font-weight: bold;")
        btn_set.clicked.connect(self.setup_table); cfg_l.addRow(btn_set); left_layout.addWidget(cfg)

        self.table = QTableWidget(0, 11); self.table.verticalHeader().setVisible(False)
        self.headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
        self.table.setColumnCount(11); self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        left_layout.addWidget(self.table)

        b_l = QHBoxLayout()
        self.btn_lq = QPushButton('BẮT ĐẦU ĐO L-Q'); self.btn_lq.setFixedHeight(55); self.btn_lq.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
        self.btn_lq.clicked.connect(lambda: self.start_measure("LQ"))
        self.btn_r = QPushButton('BẮT ĐẦU ĐO R'); self.btn_r.setFixedHeight(55); self.btn_r.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_r.clicked.connect(lambda: self.start_measure("R"))
        b_l.addWidget(self.btn_lq); b_l.addWidget(self.btn_r); left_layout.addLayout(b_l)

        self.lbl_msg = QLabel("CHỜ KẾT NỐI..."); self.lbl_msg.setAlignment(Qt.AlignCenter); self.lbl_msg.setStyleSheet("color: gray; font-weight: bold; font-size: 26pt; padding: 5px;")
        left_layout.addWidget(self.lbl_msg)

        self.log_box = QTextEdit(); self.log_box.setFixedHeight(60); self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background-color: #ffffff; color: #000000; font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
        left_layout.addWidget(self.log_box)

        self.btn_export = QPushButton('XUẤT BÁO CÁO CSV'); self.btn_export.setFixedHeight(40); self.btn_export.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self.export_csv); left_layout.addWidget(self.btn_export)
        main_layout.addWidget(left_container, 65)

        # --- CỘT PHẢI (35%) ---
        right_container = QGroupBox("Phân Tích Chất Lượng")
        right_container.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 12px; background-color: white; margin-top: 15px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; background-color: white; }
        """)
        right_layout = QVBoxLayout(right_container)
        self.lbl_chart_title = QLabel("TỶ LỆ %"); self.lbl_chart_title.setAlignment(Qt.AlignCenter); self.lbl_chart_title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #333; margin-bottom: 5px;")
        right_layout.addWidget(self.lbl_chart_title)
        self.chart = MplsChart(self); right_layout.addWidget(self.chart, 5)
        self.lbl_p, self.lbl_f, self.lbl_w = QLabel("PASS: 0"), QLabel("FAIL: 0"), QLabel("WARNING: 0")
        for lbl, c in zip([self.lbl_p, self.lbl_f, self.lbl_w], ['#4CAF50', '#F44336', '#FFEB3B']):
            lbl.setFixedHeight(50); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet(f"background-color: {c}; color: {'white' if c!='#FFEB3B' else 'black'}; border-radius: 10px; font-weight: bold; font-size: 14pt; margin-bottom: 5px;")
            right_layout.addWidget(lbl)
        main_layout.addWidget(right_container, 35)

        self.update_pns(); self.update_chart()

    def update_pns(self):
        self.cb_pn.clear()
        if not self.df_database.empty:
            p = self.df_database[self.df_database['LINE'] == self.cb_line.currentText()]['PART NUMBER'].unique().astype(str)
            self.cb_pn.addItems(sorted(p))

    def setup_table(self):
        try:
            q = int(self.txt_qty.text()); self.table.setRowCount(q)
            for i in range(q):
                for j in range(11):
                    it = QTableWidgetItem(""); it.setTextAlignment(Qt.AlignCenter); self.table.setItem(i, j, it)
                self.table.item(i, 0).setText(str(i+1))
            self.lbl_msg.setText(f"ĐÃ TẠO {q} DÒNG"); self.update_chart()
        except: pass

    # ================== XỬ LÝ KẾT NỐI AN TOÀN ==================
    def connect_device(self):
        port = self.cb_ports.currentText()
        if not port:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn cổng COM!")
            return
        
        try:
            # Thiết lập timeout ngắn để kiểm tra phản hồi
            self.ser = serial.Serial(port, 9600, timeout=1.5)
            self.ser.write(b"*IDN?\r\n")
            time.sleep(0.2)
            idn = self.ser.readline().decode('ascii').strip()
            
            if idn:
                self.lbl_msg.setText("ĐÃ KẾT NỐI"); self.lbl_msg.setStyleSheet("color: green; font-weight: bold; font-size: 26pt;")
                self.btn_conn.setEnabled(False); self.btn_disconn.setEnabled(True)
                self.log_box.append(f"Thiết bị: {idn}")
            else:
                self.ser.close(); self.ser = None
                QMessageBox.critical(self, "Lỗi kết nối", "Máy đo không phản hồi. Vui lòng kiểm tra dây cáp và máy đo!")
        except Exception as e:
            if self.ser: self.ser.close(); self.ser = None
            QMessageBox.critical(self, "Lỗi Serial", f"Không thể mở cổng {port}.\nChi tiết: {str(e)}")

    def disconnect_device(self):
        if self.ser and self.ser.is_open:
            try:
                # Gửi lệnh trả máy về chế độ LOCAL
                self.ser.write(b":SYSTem:LOCAL\r\n") 
                time.sleep(0.1)
                self.ser.close()
            except: pass
        
        self.ser = None
        self.btn_conn.setEnabled(True); self.btn_disconn.setEnabled(False)
        self.lbl_msg.setText("ĐÃ NGẮT KẾT NỐI"); self.lbl_msg.setStyleSheet("color: red; font-weight: bold; font-size: 26pt;")
        self.log_box.append("Hệ thống đã ngắt kết nối và thoát chế độ Remote.")

    def start_measure(self, mode):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối máy đo!"); return
        pn = self.cb_pn.currentText(); specs = self.df_database[self.df_database['PART NUMBER'] == pn].iloc[0]
        self.worker = MeasureWorker(self.ser, specs, self.table.rowCount(), mode)
        self.worker.data_signal.connect(self.on_data); self.worker.row_signal.connect(self.on_row)
        self.worker.msg_signal.connect(self.lbl_msg.setText); self.worker.raw_signal.connect(self.log_box.append); self.worker.start()

    def on_data(self, r, c, v1, v2, clr, st):
        it1 = self.table.item(r, c)
        if it1: it1.setText(f"{v1:.3f}"); it1.setBackground(clr)
        if c in [1,3,5]:
            it2 = self.table.item(r, c+1)
            if it2: it2.setText(f"{v2:.2f}"); it2.setBackground(clr)
        self.table.scrollToItem(it1)

    def on_row(self, r, st, clr):
        it = self.table.item(r, 10); it.setText(st); it.setBackground(clr); self.update_chart()

    def update_chart(self):
        p, f, w = 0, 0, 0
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 10)
            if it and it.text() != "":
                if it.text() == "PASS": p += 1
                elif it.text() == "FAIL": f += 1
                elif it.text() == "WARNING": w += 1
        total = (p+f+w) or 1
        self.chart.axes.clear(); self.chart.axes.pie([p,f,w] if (p+f+w)>0 else [1], colors=['#4CAF50','#F44336','#FFEB3B'] if (p+f+w)>0 else ['#eee'], startangle=90, wedgeprops=dict(width=0.45))
        self.chart.draw()
        self.lbl_p.setText(f"PASS: {p}"); self.lbl_f.setText(f"FAIL: {f}"); self.lbl_w.setText(f"WARNING: {w}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu báo cáo", f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f); writer.writerow(self.headers)
                for r in range(self.table.rowCount()):
                    writer.writerow([self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(11)])
            QMessageBox.information(self, "Xong", "Đã xuất báo cáo.")

    def refresh_ports(self):
        self.cb_ports.clear()
        for p in serial.tools.list_ports.comports(): self.cb_ports.addItem(p.device)

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = LCRApp(); ex.show(); sys.exit(app.exec_())