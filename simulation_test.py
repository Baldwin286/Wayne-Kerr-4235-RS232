import sys
import time
import csv
import random
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

# ================== LỚP TỰ XÓA SỐ 0 KHI NHẤP CHUỘT ==================
class AutoClearLineEdit(QLineEdit):
    def focusInEvent(self, event):
        if self.text() == "0":
            self.clear()
        super().focusInEvent(event)

# ================== LUỒNG ĐO MÔ PHỎNG (LOGIC THỰC TẾ) ==================
class MeasureWorker(QThread):
    data_signal = pyqtSignal(int, int, float, float, QColor, str)
    row_signal = pyqtSignal(int, str, QColor)
    msg_signal = pyqtSignal(str)
    raw_signal = pyqtSignal(str) # Gửi log thô về UI

    def __init__(self, specs, total_qty, mode="LQ"):
        super().__init__()
        self.specs, self.total_qty, self.mode = specs, total_qty, mode
        self.is_running = True

    def run(self):
        try:
            if self.mode == "LQ": self.simulate_lq()
            else: self.simulate_r()
        except Exception as e: self.msg_signal.emit(f"Lỗi: {e}")

    def evaluate(self, val, s_min, s_center, s_max, q_val, q_limit):
        # 1. FAIL: Nằm ngoài dải Min-Max HOẶC Q thấp hơn Qmin
        if val < s_min or val > s_max or q_val < q_limit:
            return "FAIL", QColor(244, 67, 54) # Đỏ rực
        
        # 2. WARNING: Nằm trong dải nhưng ở vùng 15% biên
        margin = (s_max - s_min) * 0.15
        if (val <= s_min + margin) or (val >= s_max - margin):
            return "WARNING", QColor(255, 235, 59) # Vàng
            
        # 3. PASS: Gần Center
        return "PASS", QColor(76, 175, 80) # Xanh lá

    def simulate_lq(self):
        for row in range(self.total_qty):
            if not self.is_running: break
            row_evals = []
            for pair_idx, axis in zip([1, 3, 5], ['LX', 'LY', 'LZ']):
                s_min, s_center, s_max = float(self.specs[f"{axis}_MIN"]), float(self.specs[f"{axis}_CENTER"]), float(self.specs[f"{axis}_MAX"])
                q_limit = float(self.specs.get(f"Q{axis[-1]}_MIN", 0))

                stb, last_val = 0, 0
                while self.is_running:
                    time.sleep(0.3)
                    seed = random.random()
                    
                    # GIẢ LẬP CÁC TRƯỜNG HỢP THỰC TẾ
                    if seed > 0.3: # 70% trường hợp: Kẹp kim đo thật (E-3)
                        # Có 10% trong số đó là linh kiện HỎNG NẶNG (Fail ngoài dải 50%)
                        if random.random() < 0.1:
                            v_l_mh = random.choice([s_min * 0.4, s_max * 1.8])
                            v_q = q_limit * 0.5
                        else: # Linh kiện bình thường (Pass/Warn/Fail nhẹ)
                            v_l_mh = random.uniform(s_min * 0.9, s_max * 1.1)
                            v_q = random.uniform(q_limit - 1, q_limit + 10)
                        
                        raw_line = f"{v_l_mh / 1000:.6E} , {v_q:.2f}"
                    else: # 30% trường hợp: Chưa chạm kim - Số rác (E+3)
                        raw_line = f"{random.uniform(-150, 150):.3f}E+3 , 0.50"

                    self.raw_signal.emit(raw_line) # Hiện log thô lên giao diện
                    
                    # LOGIC LỌC: Chỉ nhận nếu là đơn vị mH (Henry nhỏ)
                    v_l_conv = float(raw_line.split(',')[0]) * 1000
                    v_q_conv = float(raw_line.split(',')[1])

                    # Nếu giá trị lọt vào vùng đo (nhỏ hơn 500mH chẳng hạn) -> Chấp nhận hết để check Fail
                    if abs(v_l_conv) < 500:
                        self.msg_signal.emit(f"LK {row+1}: {axis} - ĐANG CHỐT SỐ...")
                        if abs(v_l_conv - last_val) < 0.1: stb += 1
                        else: stb = 0
                        last_val = v_l_conv
                        
                        if stb >= 2:
                            st, clr = self.evaluate(v_l_conv, s_min, s_center, s_max, v_q_conv, q_limit)
                            self.data_signal.emit(row, pair_idx, v_l_conv, v_q_conv, clr, st)
                            row_evals.append(st); break
                    else:
                        self.msg_signal.emit(f"LK {row+1}: {axis} - CHỜ KẸP KIM...")

                self.msg_signal.emit(f"LK {row+1}: {axis} OK - NHẤC KIM!")
                time.sleep(0.7)

            f = "FAIL" if "FAIL" in row_evals else ("WARNING" if "WARNING" in row_evals else "PASS")
            self.row_signal.emit(row, f, QColor(76,175,80) if f=="PASS" else (QColor(244,67,54) if f=="FAIL" else QColor(255,235,59)))

    def simulate_r(self):
        for row in range(self.total_qty):
            for i, axis in enumerate(['RX', 'RY', 'RZ']):
                self.msg_signal.emit(f"LK {row+1}: ĐO {axis}...")
                time.sleep(0.6)
                s_min, s_max = float(self.specs[f"{axis}_MIN"]), float(self.specs[f"{axis}_MAX"])
                val_r = random.uniform(s_min * 0.95, s_max * 1.05)
                st, clr = self.evaluate(val_r, s_min, (s_min+s_max)/2, s_max, 999, 0)
                self.data_signal.emit(row, 7 + i, val_r, 0, clr, st)

# --- BIỂU ĐỒ ---
class MplsChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5), dpi=100); self.axes = self.fig.add_subplot(111)
        super(MplsChart, self).__init__(self.fig)

# ================== GIAO DIỆN CHÍNH ==================
class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.df_database = pd.DataFrame()
        self.load_database(); self.initUI()

    def load_database(self):
        try:
            self.df_database = pd.read_excel(r'F:\TTTN\auto_measure_LCR\data_test.xlsx')
            self.df_database['Line'] = self.df_database['Line'].ffill()
            self.df_database.columns = self.df_database.columns.str.strip().str.upper()
        except: pass

    def initUI(self):
        self.setWindowTitle('QC LCR - Wayne Kerr 4235 (Mô phỏng Thực tế)')
        self.resize(1600, 950); self.setStyleSheet("background-color: #f5f5f5;")
        main_layout = QHBoxLayout(self)

        # --- CỘT TRÁI (65%) ---
        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)

        cfg = QGroupBox("Điều Khiển Hệ Thống")
        cfg.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 15px; padding-top: 10px; }")
        cfg_layout = QFormLayout(cfg)
        self.cb_line, self.cb_pn, self.txt_qty = QComboBox(), QComboBox(), AutoClearLineEdit()
        self.txt_qty.setText("0")
        if not self.df_database.empty: self.cb_line.addItems(sorted(self.df_database['LINE'].unique().astype(str)))
        self.cb_line.currentTextChanged.connect(self.update_pns)
        cfg_layout.addRow("Line sản xuất:", self.cb_line); cfg_layout.addRow("Mã linh kiện:", self.cb_pn); cfg_layout.addRow("Số lượng:", self.txt_qty)
        btn_set = QPushButton("KHỞI TẠO BẢNG"); btn_set.setFixedHeight(35); btn_set.clicked.connect(self.setup_table)
        cfg_layout.addRow(btn_set); left_layout.addWidget(cfg)

        self.table = QTableWidget(0, 11); self.table.verticalHeader().setVisible(False)
        self.headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
        self.table.setColumnCount(11); self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        left_layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        self.btn_lq = QPushButton('BẮT ĐẦU ĐO L-Q'); self.btn_lq.setFixedHeight(55); self.btn_lq.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
        self.btn_lq.clicked.connect(lambda: self.start_measure("LQ"))
        self.btn_r = QPushButton('BẮT ĐẦU ĐO R'); self.btn_r.setFixedHeight(55); self.btn_r.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_r.clicked.connect(lambda: self.start_measure("R"))
        btn_box.addWidget(self.btn_lq); btn_box.addWidget(self.btn_r); left_layout.addLayout(btn_box)

        self.lbl_msg = QLabel("HỆ THỐNG SẴN SÀNG"); self.lbl_msg.setAlignment(Qt.AlignCenter); self.lbl_msg.setStyleSheet("color: red; font-weight: bold; font-size: 26pt;")
        left_layout.addWidget(self.lbl_msg)

        # RAW DATA LOG (Góc dưới trái)
        self.log_box = QTextEdit(); self.log_box.setFixedHeight(60); self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Dữ liệu thô từ máy đo..."); left_layout.addWidget(self.log_box)

        self.btn_export = QPushButton('XUẤT BÁO CÁO CSV'); self.btn_export.setFixedHeight(40); self.btn_export.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self.export_csv); left_layout.addWidget(self.btn_export)
        main_layout.addWidget(left_container, 65)

        # --- CỘT PHẢI (35%) ---
        right_container = QGroupBox("Phân Tích Chất Lượng")
        right_container.setStyleSheet("background-color: white; border-radius: 12px; font-weight: bold;")
        right_layout = QVBoxLayout(right_container)
        self.chart = MplsChart(self); right_layout.addWidget(self.chart, 5)
        self.lbl_p, self.lbl_f, self.lbl_w = QLabel("PASS: 0"), QLabel("FAIL: 0"), QLabel("WARNING: 0")
        for lbl, c in zip([self.lbl_p, self.lbl_f, self.lbl_w], ['#4CAF50', '#F44336', '#FFEB3B']):
            lbl.setFixedHeight(45); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet(f"background-color: {c}; border-radius: 8px;")
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
            self.lbl_msg.setText(f"SẴN SÀNG ĐO {q} LK")
        except: pass

    def start_measure(self, mode):
        if self.cb_pn.currentText() == "": return
        specs = self.df_database[self.df_database['PART NUMBER'] == self.cb_pn.currentText()].iloc[0]
        self.worker = MeasureWorker(specs, self.table.rowCount(), mode)
        self.worker.data_signal.connect(self.on_data); self.worker.row_signal.connect(self.on_row); 
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
            txt = self.table.item(r, 10).text()
            if txt == "PASS": p += 1
            elif txt == "FAIL": f += 1
            elif txt == "WARNING": w += 1
        total = (p+f+w) or 1
        self.chart.axes.clear(); self.chart.axes.pie([p,f,w] if (p+f+w)>0 else [1], colors=['#4CAF50','#F44336','#FFEB3B'] if (p+f+w)>0 else ['#eee'], startangle=90, wedgeprops=dict(width=0.45))
        self.chart.draw()
        self.lbl_p.setText(f"PASS: {p} ({(p/total)*100:.1f}%)"); self.lbl_f.setText(f"FAIL: {f} ({(f/total)*100:.1f}%)"); self.lbl_w.setText(f"WARNING: {w} ({(w/total)*100:.1f}%)")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu báo cáo", f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f); writer.writerow(self.headers)
                for r in range(self.table.rowCount()):
                    writer.writerow([self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(11)])
            QMessageBox.information(self, "Xong", "Đã xuất báo cáo.")

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = LCRApp(); ex.show(); sys.exit(app.exec_())