import sys
import os
import glob # Thư viện để tìm kiếm file theo mẫu
import pandas as pd
from datetime import datetime # Thư viện xử lý thời gian (Bị thiếu dẫn đến lỗi của bạn)
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QHBoxLayout, QFrame, QMessageBox)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

# Đường dẫn thư mục chứa dữ liệu
DATA_PATH = r"F:\TTTN\auto_measure_LCR\CSV_data\3DC_30022026"

try:
    from test_interface_LQ import LCRApp as LQWindow
    from test_interface_Rdc import RdcApp as RWindow
except ImportError:
    print("Lưu ý: Hãy đảm bảo các file giao diện nằm cùng thư mục!")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QC MEASUREMENT SYSTEM - PREMO')
        self.setMinimumSize(600, 600) 
        self.setStyleSheet("background-color: #f5f5f5;") 

        outer_layout = QVBoxLayout()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(50, 30, 50, 50)
        content_layout.setSpacing(15)

        # 1. LOGO
        logo_label = QLabel()
        pixmap = QPixmap('premo_logo.jpg') 
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(250, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("COMPANY LOGO")
            logo_label.setStyleSheet("font-size: 20pt; color: #9e9e9e; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(logo_label)

        # 2. TIÊU ĐỀ
        title = QLabel("HỆ THỐNG QUẢN LÝ ĐO QC")
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; margin-top: 10px;")
        content_layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        content_layout.addWidget(line)
        content_layout.addSpacing(10)

        btn_style = """
            QPushButton {
                background-color: %s;
                color: white;
                border-radius: 12px;
                font-size: 13pt;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover { background-color: %s; }
        """

        # 3. NÚT ĐO L-Q
        self.btn_lq = QPushButton("  1. ĐO THÔNG SỐ L - Q")
        self.btn_lq.setFixedHeight(80)
        self.btn_lq.setMinimumWidth(450)
        self.btn_lq.setStyleSheet(btn_style % ("#2196F3", "#1976D2"))
        self.btn_lq.clicked.connect(self.open_lq)
        content_layout.addWidget(self.btn_lq, 0, Qt.AlignCenter)

        # 4. NÚT ĐO R
        self.btn_r = QPushButton("  2. ĐO ĐIỆN TRỞ Rdc")
        self.btn_r.setFixedHeight(80)
        self.btn_r.setMinimumWidth(450)
        self.btn_r.setStyleSheet(btn_style % ("#EF6C00", "#E65100"))
        self.btn_r.clicked.connect(self.open_r)
        content_layout.addWidget(self.btn_r, 0, Qt.AlignCenter)

        # 5. NÚT MERGE FILE
        self.btn_merge = QPushButton("  3. GỘP DỮ LIỆU (MERGE CSV)")
        self.btn_merge.setFixedHeight(80)
        self.btn_merge.setMinimumWidth(450)
        self.btn_merge.setStyleSheet(btn_style % ("#4CAF50", "#388E3C"))
        self.btn_merge.clicked.connect(self.merge_csv_files)
        content_layout.addWidget(self.btn_merge, 0, Qt.AlignCenter)

        # 6. FOOTER
        footer = QLabel("© 2026 Production Engineering Dept")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #757575; font-size: 9pt; margin-top: 20px;")
        main_layout_final = QVBoxLayout() # Sửa lỗi nhỏ về layout
        content_layout.addWidget(footer)

        outer_layout.addStretch(1)
        outer_layout.addLayout(content_layout)
        outer_layout.addStretch(1)
        self.setLayout(outer_layout)

        self.lq_window = None
        self.r_window = None

    def merge_csv_files(self):
        """Hàm tự động tìm 2 file mới nhất và gộp thành Finalreport_timestamp.csv"""
        # Tìm tất cả file đo trong thư mục
        list_lq = glob.glob(os.path.join(DATA_PATH, "file1_LQ_*.csv"))
        list_r = glob.glob(os.path.join(DATA_PATH, "file2_Rdc_*.csv"))

        if not list_lq or not list_r:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy file đo phù hợp để gộp!")
            return

        # Lấy file mới nhất dựa trên thời gian tạo
        file_lq = max(list_lq, key=os.path.getctime)
        file_r = max(list_r, key=os.path.getctime)

        # Tạo tên file Final với Timestamp
        now = datetime.now()
        timestamp_str = now.strftime("%d%m%Y_%H%M")
        filename_final = f"Finalreport_{timestamp_str}.csv"
        file_output = os.path.join(DATA_PATH, filename_final)

        try:
            # Đọc Header (Dòng log đầu tiên)
            with open(file_lq, 'r', encoding='utf-8-sig') as f:
                header_lq = f.readline().strip()
            with open(file_r, 'r', encoding='utf-8-sig') as f:
                header_r = f.readline().strip()

            # Đọc dữ liệu bảng (skiprows=1)
            df_lq = pd.read_csv(file_lq, skiprows=1)
            df_r = pd.read_csv(file_r, skiprows=1)

            # Gộp dữ liệu bảng dựa trên STT
            merged_df = pd.merge(df_lq, df_r, on="STT", how="inner")

            # Thứ tự cột yêu cầu
            cols_order = [
                'STT', 
                'Lx (mH)', 'Qx', 'Ly (mH)', 'Qy', 'Lz (mH)', 'Qz', 
                'Rx (Ω)', 'Ry (Ω)', 'Rz (Ω)', 
                'STATUS LQ', 'STATUS Rdc'
            ]
            
            existing_cols = [c for c in cols_order if c in merged_df.columns]
            final_df = merged_df[existing_cols]

            # Ghi file Final (Log trước, Bảng sau)
            with open(file_output, 'w', newline='', encoding='utf-8-sig') as f:
                f.write(f"LOG LQ: {header_lq}\n")
                f.write(f"LOG Rdc: {header_r}\n")
                f.write("\n") # Dòng trống
                final_df.to_csv(f, index=False)
            
            QMessageBox.information(self, "Thành công", 
                                    f"Đã gộp thành công!\nLQ: {os.path.basename(file_lq)}\nRdc: {os.path.basename(file_r)}\n\nLưu tại: {filename_final}")
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Quá trình gộp file thất bại: {str(e)}")

    def open_lq(self):
        if self.lq_window is None:
            self.lq_window = LQWindow()
            self.lq_window.back_signal.connect(self.show_main)
        if self.isMaximized(): self.lq_window.showMaximized()
        else: self.lq_window.show()
        self.hide()

    def open_r(self):
        if self.r_window is None:
            self.r_window = RWindow()
            self.r_window.back_signal.connect(self.show_main)
        if self.isMaximized(): self.r_window.showMaximized()
        else: self.r_window.show()
        self.hide()

    def show_main(self):
        if self.isMaximized(): self.showMaximized()
        else: self.showNormal()
        self.activateWindow()
        self.raise_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())