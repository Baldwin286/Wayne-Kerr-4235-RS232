import sys
import serial
import serial.tools.list_ports
import time
import csv
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog,
                             QFrame, QGroupBox)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- Lớp biểu đồ ---
class MplsChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111)
        super(MplsChart, self).__init__(self.fig)

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.current_row = 0
        
        # --- CẤU HÌNH SPECS (Đơn vị: kH) ---
        self.L_MIN, self.L_CENTER, self.L_MAX = 6.84, 7.2, 7.56
        self.L_WARN_MARGIN = 0.1 
        self.Q_XY_MIN = 14.5
        self.Q_Z_MIN = 18.0
        self.RX_SPECS = (135, 150, 165)
        self.RY_SPECS = (144, 160, 176)
        self.RZ_SPECS = (189, 210, 231)

        # Ngưỡng phát hiện để bắt đầu lọc ổn định
        self.L_GATE = 1.0 

        self.initUI()
        self.refresh_ports()

    def initUI(self):
        self.setWindowTitle('QC Wayne Kerr 4235 - Auto kH/Q/R Measurement')
        self.resize(1550, 950)
        self.setStyleSheet("background-color: #f5f5f5;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        # PHẦN BÊN TRÁI
        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)

        conn_group = QGroupBox("Kết nối")
        conn_layout = QHBoxLayout(conn_group)
        self.combo_ports = QComboBox()
        self.btn_connect = QPushButton('Kết Nối')
        self.btn_connect.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(QLabel('Cổng:'))
        conn_layout.addWidget(self.combo_ports, 1)
        conn_layout.addWidget(self.btn_connect)
        left_layout.addWidget(conn_group)

        self.table = QTableWidget(125, 11)
        self.table.verticalHeader().setVisible(False)
        self.headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(125):
            it = QTableWidgetItem(str(i+1)); it.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, it)
        left_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_lq = QPushButton('ĐO L-Q (125 LK)')
        self.btn_lq.setFixedHeight(55)
        self.btn_lq.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
        self.btn_lq.clicked.connect(self.auto_measure_lq)
        self.btn_r = QPushButton('ĐO R (125 LK)')
        self.btn_r.setFixedHeight(55)
        self.btn_r.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_r.clicked.connect(self.auto_measure_r)
        btn_layout.addWidget(self.btn_lq)
        btn_layout.addWidget(self.btn_r)
        left_layout.addLayout(btn_layout)

        self.btn_export = QPushButton('XUẤT CSV')
        self.btn_export.clicked.connect(self.export_csv)
        left_layout.addWidget(self.btn_export)

        # ĐÃ SỬA: Đổi tên từ lbl_status thành lbl_msg để khớp với hàm đo
        self.lbl_msg = QLabel('Trạng thái: Sẵn sàng.')
        self.lbl_msg.setStyleSheet("color: #d32f2f; font-weight: bold; font-size: 12pt;")
        left_layout.addWidget(self.lbl_msg)

        # PHẦN BÊN PHẢI
        right_container = QGroupBox("Phân Tích")
        right_container.setStyleSheet("background-color: white; border-radius: 12px; font-weight: bold;")
        right_layout = QVBoxLayout(right_container)
        self.lbl_chart_title = QLabel("THỐNG KÊ %")
        self.lbl_chart_title.setAlignment(Qt.AlignCenter)
        self.lbl_chart_title.setStyleSheet("font-size: 18pt;")
        right_layout.addWidget(self.lbl_chart_title)

        self.chart = MplsChart(self)
        right_layout.addWidget(self.chart)

        self.lbl_pass = QLabel("PASS: 0 (0.0%)"); self.lbl_fail = QLabel("FAIL: 0 (0.0%)"); self.lbl_warn = QLabel("WARNING: 0 (0.0%)")
        for lbl, color in zip([self.lbl_pass, self.lbl_fail, self.lbl_warn], ['#4CAF50', '#F44336', '#FFEB3B']):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"background-color: {color}; color: {'white' if color != '#FFEB3B' else 'black'}; font-weight: bold; padding: 10px; border-radius: 5px;")
            right_layout.addWidget(lbl)
        right_layout.addStretch()

        main_layout.addWidget(left_container, 65)
        main_layout.addWidget(right_container, 35)
        self.update_chart([0, 0, 0])

    def check_lq_quality(self, val_l, val_q, is_z=False):
        q_limit = self.Q_Z_MIN if is_z else self.Q_XY_MIN
        if val_l < self.L_MIN or val_l > self.L_MAX or val_q < q_limit:
            return "FAIL", QColor(255, 204, 204)
        if (val_l < self.L_MIN + self.L_WARN_MARGIN) or (val_l > self.L_MAX - self.L_WARN_MARGIN):
            return "WARNING", QColor(255, 255, 204)
        return "PASS", QColor(204, 255, 204)

    def auto_measure_lq(self):
        if not self.ser: return
        self.ser.write(b":MEAS:FUNC1 L\n:MEAS:FUNC2 Q\n")
        self.current_row = 0
        while self.current_row < 125:
            self.table.selectRow(self.current_row)
            row_evals = []
            for pair_idx in [1, 3, 5]: 
                self.lbl_msg.setText(f"LK {self.current_row+1}: Chờ kẹp {self.headers[pair_idx]}...")
                stable_count, last_l = 0, 0
                
                while True:
                    self.ser.write(b":MEAS:TRIGger\n")
                    time.sleep(0.1)
                    line = self.ser.readline().decode('ascii').strip()
                    if line and ',' in line:
                        try:
                            parts = line.split(',')
                            l_kh = float(parts[0]) * 1000 # Giả sử máy trả Henry -> đổi sang kH
                            q_val = float(parts[1])

                            if self.L_MIN * 0.8 <= l_kh <= self.L_MAX * 1.2:
                                if abs(l_kh - last_l) < 0.02: stable_count += 1
                                else: stable_count = 0
                                last_l = l_kh
                                
                                if stable_count >= 3: 
                                    it_l = QTableWidgetItem(f"{l_kh:.3f}"); it_q = QTableWidgetItem(f"{q_val:.2f}")
                                    it_l.setTextAlignment(Qt.AlignCenter); it_q.setTextAlignment(Qt.AlignCenter)
                                    st, color = self.check_lq_quality(l_kh, q_val, is_z=(pair_idx==5))
                                    it_l.setBackground(color); it_q.setBackground(color)
                                    self.table.setItem(self.current_row, pair_idx, it_l)
                                    self.table.setItem(self.current_row, pair_idx + 1, it_q)
                                    row_evals.append(st); break
                            else: stable_count = 0
                        except: pass
                    QApplication.processEvents()

                self.lbl_msg.setText(f"LK {self.current_row+1}: RÚT KIM!")
                while True:
                    self.ser.write(b":MEAS:TRIGger\n")
                    time.sleep(0.1)
                    line = self.ser.readline().decode('ascii').strip()
                    try:
                        if line and (float(line.split(',')[0])*1000) < (self.L_MIN * 0.5): break
                    except: break
                    QApplication.processEvents()

            final = "FAIL" if "FAIL" in row_evals else ("WARNING" if "WARNING" in row_evals else "PASS")
            it_st = QTableWidgetItem(final); it_st.setTextAlignment(Qt.AlignCenter)
            color_st = QColor(76,175,80) if final=="PASS" else (QColor(244,67,54) if final=="FAIL" else QColor(255,235,59))
            it_st.setBackground(color_st); self.table.setItem(self.current_row, 10, it_st)
            self.update_chart(self.get_statistics())
            self.current_row += 1
        self.lbl_msg.setText("XONG L-Q!")

    def auto_measure_r(self):
        if not self.ser: return
        self.ser.write(b":MEAS:FUNC1 R\n:MEAS:FUNC2 NONE\n")
        r_specs = [self.RX_SPECS, self.RY_SPECS, self.RZ_SPECS]
        self.current_row = 0
        while self.current_row < 125:
            self.table.selectRow(self.current_row)
            for i, col in enumerate([7, 8, 9]):
                self.lbl_msg.setText(f"LK {self.current_row+1}: Chờ đo {self.headers[col]}...")
                min_r, mid_r, max_r = r_specs[i]
                while True:
                    self.ser.write(b":MEAS:TRIGger\n")
                    time.sleep(0.15)
                    line = self.ser.readline().decode('ascii').strip()
                    try:
                        r = float(line.split(',')[0])
                        if r < 500: # Ngưỡng phát hiện kẹp kim
                            it_r = QTableWidgetItem(f"{r:.2f}"); it_r.setTextAlignment(Qt.AlignCenter)
                            color = QColor(204, 255, 204) if min_r <= r <= max_r else QColor(255, 204, 204)
                            it_r.setBackground(color); self.table.setItem(self.current_row, col, it_r); break
                    except: pass
                    QApplication.processEvents()
                while True:
                    self.ser.write(b":MEAS:TRIGger\n")
                    time.sleep(0.1); line = self.ser.readline().decode('ascii').strip()
                    try:
                        if line and float(line.split(',')[0]) > 500: break
                    except: break
                    QApplication.processEvents()
            self.current_row += 1

    def update_chart(self, stats):
        self.chart.axes.clear()
        total = sum(stats)
        if total == 0: self.chart.axes.pie([1], colors=['#e0e0e0'], startangle=90, wedgeprops=dict(width=0.4))
        else:
            self.chart.axes.pie(stats, colors=['#4CAF50', '#F44336', '#FFEB3B'], startangle=90, wedgeprops=dict(width=0.4))
            p, f, w = [(s/total)*100 for s in stats]
            self.lbl_pass.setText(f"PASS: {stats[0]} ({p:.1f}%)"); self.lbl_fail.setText(f"FAIL: {stats[1]} ({f:.1f}%)"); self.lbl_warn.setText(f"WARNING: {stats[2]} ({w:.1f}%)")
        self.chart.draw()

    def get_statistics(self):
        p, f, w = 0, 0, 0
        for r in range(125):
            it = self.table.item(r, 10)
            if it:
                if it.text() == "PASS": p += 1
                elif it.text() == "FAIL": f += 1
                elif it.text() == "WARNING": w += 1
        return [p, f, w]

    def export_csv(self):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file", f"Bao_cao_QC_{now}.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f); writer.writerow(self.headers)
                for r in range(125): writer.writerow([self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(11)])
            QMessageBox.information(self, "Xong", "Đã xuất báo cáo.")

    def toggle_connection(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.combo_ports.currentText(), 9600, timeout=1)
                self.btn_connect.setText("Ngắt Kết Nối"); self.btn_connect.setStyleSheet("background-color: #d32f2f; color: white;")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))
        else: self.ser.close(); self.ser = None; self.btn_connect.setText("Kết Nối"); self.btn_connect.setStyleSheet("")

    def refresh_ports(self):
        self.combo_ports.clear()
        for p in serial.tools.list_ports.comports(): self.combo_ports.addItem(p.device)

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = LCRApp(); ex.show(); sys.exit(app.exec_())