# import sys
# import time
# import csv
# import random
# from datetime import datetime # Thêm thư viện để lấy thời gian
# from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
#                              QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
#                              QHBoxLayout, QHeaderView, QMessageBox, QFileDialog,
#                              QFrame, QGroupBox)
# from PyQt5.QtGui import QColor, QFont
# from PyQt5.QtCore import Qt
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure

# # --- Lớp biểu đồ ---
# class MplsChart(FigureCanvas):
#     def __init__(self, parent=None):
#         self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#ffffff')
#         self.axes = self.fig.add_subplot(111)
#         super(MplsChart, self).__init__(self.fig)

# class LCRApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.current_row = 0
#         self.L_LOWER = 90e-6
#         self.L_UPPER = 110e-6
#         self.L_WARN_ZONE = 3e-6 

#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('Hệ Thống Kiểm Soát Chất Lượng Linh Kiện - Wayne Kerr 4235')
#         self.resize(1550, 900)
#         self.setStyleSheet("background-color: #f5f5f5;")

#         main_layout = QHBoxLayout(self)
#         main_layout.setContentsMargins(15, 15, 15, 15)
#         main_layout.setSpacing(20)

#         # --- BÊN TRÁI: BẢNG & ĐIỀU KHIỂN ---
#         left_container = QFrame()
#         left_layout = QVBoxLayout(left_container)

#         self.table = QTableWidget(125, 11)
#         self.table.verticalHeader().setVisible(False)
#         self.headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
#         self.table.setHorizontalHeaderLabels(self.headers)
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
#         # Khởi tạo STT căn giữa
#         for i in range(125):
#             item_stt = QTableWidgetItem(str(i+1))
#             item_stt.setTextAlignment(Qt.AlignCenter)
#             self.table.setItem(i, 0, item_stt)
            
#         left_layout.addWidget(self.table)

#         # Cụm nút đo
#         btn_layout = QHBoxLayout()
#         self.btn_lq = QPushButton('BẮT ĐẦU ĐO L-Q (125 LK)')
#         self.btn_lq.setFixedHeight(55)
#         self.btn_lq.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold; font-size: 11pt;")
#         self.btn_lq.clicked.connect(self.auto_measure_lq)
        
#         self.btn_r = QPushButton('BẮT ĐẦU ĐO R (125 LK)')
#         self.btn_r.setFixedHeight(55)
#         self.btn_r.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; font-size: 11pt;")
#         self.btn_r.clicked.connect(self.auto_measure_r)
        
#         btn_layout.addWidget(self.btn_lq)
#         btn_layout.addWidget(self.btn_r)
#         left_layout.addLayout(btn_layout)

#         # Nút Xuất CSV
#         self.btn_export = QPushButton('XUẤT BÁO CÁO CSV DỮ LIỆU')
#         self.btn_export.setFixedHeight(45)
#         self.btn_export.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold; font-size: 10pt;")
#         self.btn_export.clicked.connect(self.export_csv)
#         left_layout.addWidget(self.btn_export)

#         self.lbl_msg = QLabel("Trạng thái: Sẵn sàng.")
#         self.lbl_msg.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
#         left_layout.addWidget(self.lbl_msg)

#         # --- BÊN PHẢI: BIỂU ĐỒ & CHÚ THÍCH ---
#         right_container = QGroupBox("Phân Tích Chất Lượng")
#         right_container.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 12px; background-color: white; }")
#         right_layout = QVBoxLayout(right_container)

#         self.lbl_chart_title = QLabel("THỐNG KÊ TỶ LỆ %")
#         self.lbl_chart_title.setAlignment(Qt.AlignCenter)
#         self.lbl_chart_title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #333; margin: 15px 0;")
#         right_layout.addWidget(self.lbl_chart_title)

#         self.chart = MplsChart(self)
#         right_layout.addWidget(self.chart)

#         # Chú thích 3 ô màu (Số lượng + %)
#         self.lbl_pass = QLabel("PASS: 0 (0.0%)")
#         self.lbl_pass.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14pt; padding: 12px; border-radius: 8px;")
#         self.lbl_pass.setAlignment(Qt.AlignCenter)
        
#         self.lbl_fail = QLabel("FAIL: 0 (0.0%)")
#         self.lbl_fail.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; font-size: 14pt; padding: 12px; border-radius: 8px;")
#         self.lbl_fail.setAlignment(Qt.AlignCenter)
        
#         self.lbl_warn = QLabel("WARNING: 0 (0.0%)")
#         self.lbl_warn.setStyleSheet("background-color: #FFEB3B; color: #333; font-weight: bold; font-size: 14pt; padding: 12px; border-radius: 8px;")
#         self.lbl_warn.setAlignment(Qt.AlignCenter)

#         right_layout.addWidget(self.lbl_pass)
#         right_layout.addWidget(self.lbl_fail)
#         right_layout.addWidget(self.lbl_warn)
#         right_layout.addStretch()

#         main_layout.addWidget(left_container, 65)
#         main_layout.addWidget(right_container, 35)

#         self.update_chart([0, 0, 0])

#     def update_chart(self, stats):
#         self.chart.axes.clear()
#         total = sum(stats)
#         if total == 0:
#             self.chart.axes.pie([1], colors=['#e0e0e0'], startangle=90, wedgeprops=dict(width=0.4))
#             self.lbl_pass.setText("PASS: 0 (0.0%)")
#             self.lbl_fail.setText("FAIL: 0 (0.0%)")
#             self.lbl_warn.setText("WARNING: 0 (0.0%)")
#         else:
#             self.chart.axes.pie(stats, colors=['#4CAF50', '#F44336', '#FFEB3B'], startangle=90, wedgeprops=dict(width=0.4))
#             p_pc = (stats[0]/total)*100
#             f_pc = (stats[1]/total)*100
#             w_pc = (stats[2]/total)*100
#             self.lbl_pass.setText(f"PASS: {stats[0]} ({p_pc:.1f}%)")
#             self.lbl_fail.setText(f"FAIL: {stats[1]} ({f_pc:.1f}%)")
#             self.lbl_warn.setText(f"WARNING: {stats[2]} ({w_pc:.1f}%)")
#         self.chart.draw()

#     def get_statistics(self):
#         p, f, w = 0, 0, 0
#         for r in range(125):
#             item = self.table.item(r, 10)
#             if item:
#                 if item.text() == "PASS": p += 1
#                 elif item.text() == "FAIL": f += 1
#                 elif item.text() == "WARNING": w += 1
#         return [p, f, w]

#     def auto_measure_lq(self):
#         self.current_row = 0
#         while self.current_row < 125:
#             self.table.selectRow(self.current_row)
#             row_evals = []
#             for pair_idx in [1, 3, 5]: 
#                 time.sleep(0.05) # Giảm sleep để test nhanh hơn
#                 val_l = random.uniform(85e-6, 115e-6)
#                 val_q = random.uniform(0.1, 0.6)
                
#                 item_l = QTableWidgetItem(f"{val_l:.3e}")
#                 item_q = QTableWidgetItem(f"{val_q:.2f}")
#                 item_l.setTextAlignment(Qt.AlignCenter)
#                 item_q.setTextAlignment(Qt.AlignCenter)
                
#                 if val_l < self.L_LOWER or val_l > self.L_UPPER: 
#                     st, color = "FAIL", QColor(255, 204, 204)
#                 elif val_l < self.L_LOWER+self.L_WARN_ZONE or val_l > self.L_UPPER-self.L_WARN_ZONE: 
#                     st, color = "WARNING", QColor(255, 255, 204)
#                 else: 
#                     st, color = "PASS", QColor(204, 255, 204)
                
#                 item_l.setBackground(color)
#                 item_q.setBackground(color)
                
#                 self.table.setItem(self.current_row, pair_idx, item_l)
#                 self.table.setItem(self.current_row, pair_idx+1, item_q)
#                 row_evals.append(st)
#                 QApplication.processEvents()

#             final = "FAIL" if "FAIL" in row_evals else ("WARNING" if "WARNING" in row_evals else "PASS")
#             item_st = QTableWidgetItem(final)
#             item_st.setTextAlignment(Qt.AlignCenter)
#             item_st.setBackground(QColor(76,175,80) if final=="PASS" else (QColor(244,67,54) if final=="FAIL" else QColor(255,235,59)))
#             self.table.setItem(self.current_row, 10, item_st)
#             self.update_chart(self.get_statistics())
#             QApplication.processEvents()
#             self.current_row += 1
#         self.lbl_msg.setText("HOÀN THÀNH 125 LK (L-Q)!")

#     def auto_measure_r(self):
#         self.current_row = 0
#         while self.current_row < 125:
#             self.table.selectRow(self.current_row)
#             for col_idx in [7, 8, 9]:
#                 time.sleep(0.02)
#                 item_r = QTableWidgetItem(f"{random.uniform(0.5,5):.2f}")
#                 item_r.setTextAlignment(Qt.AlignCenter)
#                 self.table.setItem(self.current_row, col_idx, item_r)
#                 QApplication.processEvents()
#             self.current_row += 1
#         self.lbl_msg.setText("HOÀN THÀNH 125 LK (R)!")

#     def export_csv(self):
#         """Hàm xuất dữ liệu ra file CSV với tên file tự động theo ngày giờ"""
#         # Lấy thời gian hiện tại
#         now = datetime.now()
#         timestamp = now.strftime("%Y%m%d_%H%M%S") # Định dạng: 20260123_115030
#         default_filename = f"Bao_cao_QC_{timestamp}.csv"

#         path, _ = QFileDialog.getSaveFileName(self, "Lưu file dữ liệu", default_filename, "CSV Files (*.csv)")
        
#         if path:
#             try:
#                 with open(path, 'w', newline='', encoding='utf-8-sig') as f:
#                     writer = csv.writer(f)
#                     writer.writerow(self.headers)
#                     for r in range(125):
#                         row_data = []
#                         for c in range(11):
#                             item = self.table.item(r, c)
#                             row_data.append(item.text() if item else "")
#                         writer.writerow(row_data)
#                 QMessageBox.information(self, "Thành công", f"Dữ liệu đã được xuất ra file:\n{path}")
#             except Exception as e:
#                 QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {e}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = LCRApp(); ex.show()
#     sys.exit(app.exec_())

import sys
import time
import csv
import random
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel, 
                             QHBoxLayout, QHeaderView, QMessageBox, QFileDialog,
                             QFrame, QGroupBox, QLineEdit, QFormLayout)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- LỚP TỰ XÓA SỐ 0 KHI NHẤP CHUỘT ---
class AutoClearLineEdit(QLineEdit):
    def focusInEvent(self, event):
        if self.text() == "0":
            self.clear()
        super().focusInEvent(event)

class MplsChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111)
        super(MplsChart, self).__init__(self.fig)

class LCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.total_qty = 0
        self.df_database = pd.DataFrame() 
        self.load_database() 
        self.initUI()

    def load_database(self):
        file_path = r'F:\TTTN\auto_measure_LCR\data_test.xlsx' 
        try:
            self.df_database = pd.read_excel(file_path)
            self.df_database['Line'] = self.df_database['Line'].ffill()
            self.df_database.columns = self.df_database.columns.str.strip().str.upper()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Database", f"Không thể đọc file:\n{str(e)}")

    def initUI(self):
        self.setWindowTitle('Hệ thống QC LCR - Logic So Sánh Center/Warning/Fail')
        self.resize(1600, 950)
        self.setStyleSheet("background-color: #f5f5f5;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ================== CỘT TRÁI ==================
        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)

        config_group = QGroupBox("Điều Khiển Hệ Thống")
        config_group.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 15px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; background-color: #f5f5f5; }
        """)
        config_layout = QFormLayout(config_group)
        
        self.cb_line = QComboBox()
        if not self.df_database.empty:
            self.cb_line.addItems(sorted(self.df_database['LINE'].unique().astype(str)))
        self.cb_line.currentTextChanged.connect(self.update_pns)
        
        self.cb_pn = QComboBox()
        self.txt_qty = AutoClearLineEdit()
        self.txt_qty.setText("0") 

        self.btn_setup = QPushButton("KHỞI TẠO BẢNG SẢN XUẤT")
        self.btn_setup.setStyleSheet("background-color: #455a64; color: white; font-weight: bold; height: 35px;")
        self.btn_setup.clicked.connect(self.setup_table)

        config_layout.addRow("Line sản xuất:", self.cb_line)
        config_layout.addRow("Mã linh kiện (PN):", self.cb_pn)
        config_layout.addRow("Số lượng (Qty):", self.txt_qty)
        config_layout.addRow(self.btn_setup)
        left_layout.addWidget(config_group)

        self.table = QTableWidget(0, 11)
        self.table.verticalHeader().setVisible(False)
        self.headers = ['STT', 'Lx', 'Qx', 'Ly', 'Qy', 'Lz', 'Qz', 'Rx', 'Ry', 'Rz', 'STATUS']
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        left_layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        self.btn_lq = QPushButton('BẮT ĐẦU ĐO L-Q')
        self.btn_lq.setFixedHeight(50)
        self.btn_lq.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
        self.btn_lq.clicked.connect(self.auto_measure_lq)
        
        self.btn_r = QPushButton('BẮT ĐẦU ĐO R')
        self.btn_r.setFixedHeight(50)
        self.btn_r.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_r.clicked.connect(self.auto_measure_r)
        btn_box.addWidget(self.btn_lq); btn_box.addWidget(self.btn_r)
        left_layout.addLayout(btn_box)

        self.lbl_msg = QLabel("HỆ THỐNG SẴN SÀNG")
        self.lbl_msg.setAlignment(Qt.AlignCenter)
        self.lbl_msg.setStyleSheet("color: red; font-weight: bold; font-size: 26pt; padding: 10px;")
        left_layout.addWidget(self.lbl_msg)

        self.btn_export = QPushButton('XUẤT BÁO CÁO CSV')
        self.btn_export.setFixedHeight(40)
        self.btn_export.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self.export_csv)
        left_layout.addWidget(self.btn_export)

        # ================== CỘT PHẢI ==================
        right_container = QGroupBox("Phân Tích Chất Lượng")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(15, 35, 15, 15)

        self.lbl_chart_title = QLabel("TỶ LỆ %")
        self.lbl_chart_title.setAlignment(Qt.AlignCenter)
        self.lbl_chart_title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #333;")
        right_layout.addWidget(self.lbl_chart_title)

        self.chart = MplsChart(self)
        right_layout.addWidget(self.chart, 5)

        self.lbl_pass = QLabel("PASS: 0 (0.0%)")
        self.lbl_fail = QLabel("FAIL: 0 (0.0%)")
        self.lbl_warn = QLabel("WARNING: 0 (0.0%)")
        
        colors = ['#4CAF50', '#F44336', '#FFEB3B']
        for i, lbl in enumerate([self.lbl_pass, self.lbl_fail, self.lbl_warn]):
            lbl.setFixedHeight(45)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"background-color: {colors[i]}; color: {'white' if i<2 else 'black'}; font-weight: bold; font-size: 13pt; border-radius: 8px;")
            right_layout.addWidget(lbl)
        
        main_layout.addWidget(left_container, 65)
        main_layout.addWidget(right_container, 35)

        self.update_pns()
        self.update_chart([0, 0, 0])

    def update_pns(self):
        line = self.cb_line.currentText()
        self.cb_pn.clear()
        if not self.df_database.empty:
            filtered_parts = self.df_database[self.df_database['LINE'] == line]['PART NUMBER'].unique().astype(str)
            self.cb_pn.addItems(sorted(filtered_parts))

    def setup_table(self):
        try:
            qty = int(self.txt_qty.text())
            if qty <= 0: return
            self.total_qty = qty
            self.table.setRowCount(qty)
            for i in range(qty):
                it = QTableWidgetItem(str(i+1))
                it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 0, it)
                for j in range(1, 11): self.table.setItem(i, j, QTableWidgetItem(""))
            self.update_chart([0, 0, 0])
            self.lbl_msg.setText(f"ĐÃ KHỞI TẠO {qty} LINH KIỆN")
        except: pass

    def evaluate_measurement(self, val, s_min, s_center, s_max, q_val, q_limit):
        """Logic so sánh: Càng gần Center càng tốt"""
        # Kiểm tra FAIL (Nằm ngoài dải Min-Max hoặc Q quá thấp)
        if val < s_min or val > s_max or q_val < q_limit:
            return "FAIL", QColor(255, 204, 204) # Màu đỏ nhạt
        
        # Tính khoảng cách đến biên (Dải Warning chiếm 15% sát biên)
        tolerance_range = (s_max - s_min)
        warning_zone = tolerance_range * 0.15
        
        # Kiểm tra WARNING (Gần Min hoặc gần Max)
        if (val <= s_min + warning_zone) or (val >= s_max - warning_zone):
            return "WARNING", QColor(255, 255, 204) # Màu vàng nhạt
        
        # Còn lại là PASS (Gần Center)
        return "PASS", QColor(204, 255, 204) # Màu xanh nhạt

    def auto_measure_lq(self):
        if self.total_qty == 0: return
        pn = self.cb_pn.currentText()
        specs = self.df_database[self.df_database['PART NUMBER'] == pn].iloc[0]
        
        self.current_row = 0
        while self.current_row < self.total_qty:
            self.table.selectRow(self.current_row)
            row_evals = []
            
            for pair_idx, axis in zip([1, 3, 5], ['LX', 'LY', 'LZ']):
                self.lbl_msg.setText(f"LK {self.current_row+1}: CHÂM KIM {axis}...")
                QApplication.processEvents()
                time.sleep(1.2) # Đo chậm lại

                s_min, s_max = specs[f"{axis}_MIN"], specs[f"{axis}_MAX"]
                s_center = specs[f"{axis}_CENTER"] if f"{axis}_CENTER" in specs else (s_min + s_max) / 2
                char = axis[-1]
                q_col = f"Q{char}_MIN" if f"Q{char}_MIN" in specs else f"Q_{char}_MIN"
                q_limit = specs[q_col]

                # Mô phỏng giá trị đo
                seed = random.random()
                if seed > 0.2: # Giả lập PASS (Gần Center)
                    l_val = random.uniform(s_center * 0.995, s_center * 1.005)
                    q_val = random.uniform(q_limit + 5, q_limit + 10)
                elif seed > 0.08: # Giả lập WARNING (Gần biên)
                    l_val = random.choice([random.uniform(s_min, s_min + (s_max-s_min)*0.1), 
                                           random.uniform(s_max - (s_max-s_min)*0.1, s_max)])
                    q_val = random.uniform(q_limit + 1, q_limit + 3)
                else: # Giả lập FAIL (Ngoài dải)
                    l_val = s_min * 0.94; q_val = q_limit - 2

                # Đánh giá dựa trên logic Center
                res, color = self.evaluate_measurement(l_val, s_min, s_center, s_max, q_val, q_limit)
                
                it_l = QTableWidgetItem(f"{l_val:.3f}")
                it_q = QTableWidgetItem(f"{q_val:.2f}")
                it_l.setTextAlignment(Qt.AlignCenter); it_q.setTextAlignment(Qt.AlignCenter)
                it_l.setBackground(color); it_q.setBackground(color)
                
                self.table.setItem(self.current_row, pair_idx, it_l)
                self.table.setItem(self.current_row, pair_idx+1, it_q)
                row_evals.append(res)
                
                self.lbl_msg.setText(f"LK {self.current_row+1}: {axis} {res} - NHẤC KIM")
                QApplication.processEvents()
                time.sleep(0.6)

            # Status tổng
            if "FAIL" in row_evals: final = "FAIL"
            elif "WARNING" in row_evals: final = "WARNING"
            else: final = "PASS"
            
            it_st = QTableWidgetItem(final); it_st.setTextAlignment(Qt.AlignCenter)
            bg_colors = {"PASS": QColor(76,175,80), "WARNING": QColor(255,235,59), "FAIL": QColor(244,67,54)}
            it_st.setBackground(bg_colors[final]); self.table.setItem(self.current_row, 10, it_st)
            
            self.update_chart(self.get_stats())
            self.current_row += 1
            QApplication.processEvents()
            
        self.lbl_msg.setText("HOÀN THÀNH ĐO L-Q!")

    def auto_measure_r(self):
        if self.total_qty == 0: return
        pn = self.cb_pn.currentText()
        specs = self.df_database[self.df_database['PART NUMBER'] == pn].iloc[0]
        r_cols = [('RX_MIN', 'RX_CENTER', 'RX_MAX'), ('RY_MIN', 'RY_CENTER', 'RY_MAX'), ('RZ_MIN', 'RZ_CENTER', 'RZ_MAX')]
        
        self.current_row = 0
        while self.current_row < self.total_qty:
            self.table.selectRow(self.current_row)
            for i, (cmin, ccenter, cmax) in enumerate(r_cols):
                axis_name = ['X', 'Y', 'Z'][i]
                self.lbl_msg.setText(f"LK {self.current_row+1}: ĐO R TẠI {axis_name}...")
                QApplication.processEvents()
                time.sleep(1.0)

                s_min, s_center, s_max = specs[cmin], specs[ccenter], specs[cmax]
                r_val = random.uniform(s_min, s_max) # Giả lập đo trong dải
                
                # Áp dụng logic Center cho điện trở (giả định Q đạt)
                res, color = self.evaluate_measurement(r_val, s_min, s_center, s_max, 100, 1)

                it = QTableWidgetItem(f"{r_val:.2f}")
                it.setTextAlignment(Qt.AlignCenter); it.setBackground(color)
                self.table.setItem(self.current_row, 7 + i, it)
                QApplication.processEvents()
            
            self.current_row += 1
        self.lbl_msg.setText("HOÀN THÀNH ĐO R!")

    def update_chart(self, stats):
        self.chart.axes.clear()
        total = sum(stats)
        if total == 0: 
            self.chart.axes.pie([1], colors=['#e0e0e0'], startangle=90, wedgeprops=dict(width=0.45))
        else:
            self.chart.axes.pie(stats, colors=['#4CAF50', '#F44336', '#FFEB3B'], startangle=90, wedgeprops=dict(width=0.45))
            p, f, w = [(s/total)*100 for s in stats]
            self.lbl_pass.setText(f"PASS: {stats[0]} ({p:.1f}%)")
            self.lbl_fail.setText(f"FAIL: {stats[1]} ({f:.1f}%)")
            self.lbl_warn.setText(f"WARNING: {stats[2]} ({w:.1f}%)")
        self.chart.draw()

    def get_stats(self):
        p, f, w = 0, 0, 0
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 10)
            if it:
                if it.text() == "PASS": p += 1
                elif it.text() == "FAIL": f += 1
                elif it.text() == "WARNING": w += 1
        return [p, f, w]

    def export_csv(self): pass

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = LCRApp(); ex.show(); sys.exit(app.exec_())