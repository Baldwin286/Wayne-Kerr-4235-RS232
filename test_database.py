import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QComboBox, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt

class SpecViewerApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. Đọc và tiền xử lý Database
        try:
            # Thay đổi đường dẫn file cho đúng với máy của bạn
            self.df = pd.read_excel(r'F:\TTTN\auto_measure_LCR\data_test.xlsx')
            
            # Xử lý các ô bị Merge ở cột Line
            self.df['Line'] = self.df['Line'].ffill()
            
            # Xóa khoảng trắng thừa ở tên cột
            self.df.columns = self.df.columns.str.strip()
        except Exception as e:
            print(f"Lỗi: {e}")
            self.df = pd.DataFrame()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # --- Khu vực chọn Line ---
        layout.addWidget(QLabel("<b>Sản xuất tại Line:</b>"))
        self.combo_line = QComboBox()
        layout.addWidget(self.combo_line)

        # --- Khu vực chọn Part Number ---
        layout.addWidget(QLabel("<b>Mã linh kiện (Part Number):</b>"))
        self.combo_part = QComboBox()
        layout.addWidget(self.combo_part)

        # --- Bảng hiển thị Specs ---
        layout.addWidget(QLabel("<b>Thông số kỹ thuật (Specs):</b>"))
        self.table_specs = QTableWidget()
        self.table_specs.setColumnCount(2)
        self.table_specs.setHorizontalHeaderLabels(["Tên thông số", "Giá trị tiêu chuẩn"])
        self.table_specs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_specs)

        # Đổ dữ liệu vào combo_line
        if not self.df.empty:
            lines = sorted(self.df['Line'].unique().astype(str))
            self.combo_line.addItems(lines)

        # Kết nối sự kiện
        self.combo_line.currentIndexChanged.connect(self.update_part_numbers)
        self.combo_part.currentIndexChanged.connect(self.display_specs)

        # Khởi tạo dữ liệu ban đầu
        self.update_part_numbers()

        self.setLayout(layout)
        self.setWindowTitle('Hệ thống quản lý Specs Sản Xuất')
        self.resize(500, 600)

    def update_part_numbers(self):
        """Cập nhật danh sách Part Number dựa trên Line đã chọn"""
        self.combo_part.blockSignals(True) # Tạm dừng sự kiện để tránh lỗi khi clear
        self.combo_part.clear()
        
        selected_line = self.combo_line.currentText()
        filtered_df = self.df[self.df['Line'] == selected_line]
        
        parts = sorted(filtered_df['Part Number'].unique().astype(str))
        self.combo_part.addItems(parts)
        self.combo_part.blockSignals(False)
        
        self.display_specs() # Cập nhật bảng ngay khi đổi Line

    def display_specs(self):
        """Hiển thị tất cả các cột Specs của Part Number đang chọn vào bảng"""
        self.table_specs.setRowCount(0)
        selected_pn = self.combo_part.currentText()
        
        if not selected_pn:
            return

        # Lấy hàng dữ liệu của Part Number được chọn
        row_data = self.df[self.df['Part Number'] == selected_pn].iloc[0]

        # Các cột không phải là Spec (để loại bỏ khỏi bảng hiển thị)
        exclude_cols = ['Line', 'Part Number']
        
        # Lặp qua tất cả các cột để đưa vào bảng
        for column_name in self.df.columns:
            if column_name not in exclude_cols:
                row_idx = self.table_specs.rowCount()
                self.table_specs.insertRow(row_idx)
                
                # Cột 0: Tên thông số (L_MIN, L_MAX...)
                item_name = QTableWidgetItem(column_name)
                # Cột 1: Giá trị từ database
                item_val = QTableWidgetItem(str(row_data[column_name]))
                
                item_val.setTextAlignment(Qt.AlignCenter)
                
                self.table_specs.setItem(row_idx, 0, item_name)
                self.table_specs.setItem(row_idx, 1, item_val)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SpecViewerApp()
    ex.show()
    sys.exit(app.exec_())