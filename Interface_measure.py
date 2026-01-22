import sys
import csv
import random
import matplotlib.pyplot as plt
import serial
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QTableWidget, QTableWidgetItem
)

class WayneKerrRS232:
    def __init__(self, port="COM7"):
        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
        time.sleep(1)

    def send(self, cmd):
        self.ser.write((cmd + '\n').encode())
        time.sleep(0.05)

    def query(self, cmd):
        self.send(cmd)
        return self.ser.readline().decode().strip()

    def setup_LQ(self):
        self.send(":MEAS:EQU-CCT SER")
        self.send(":MEAS:FREQ 1000")
        self.send(":MEAS:LEV 1.0")
        self.send(":MEAS:SPEED MED")

    def measure_LQ(self):
        """
        Đo 1 trục: L + Q
        """
        self.send(":MEAS:TRIG")
        resp = self.query(":MEAS:RES?")
        L, Q, _ = resp.split(",")
        return float(L), float(Q)

    def setup_R(self):
        self.send(":MEAS:FUNC1 RDC")

    def measure_R(self):
        self.send(":MEAS:TRIG")
        resp = self.query(":MEAS:RES?")
        R, _, _ = resp.split(",")
        return float(R)

    def close(self):
        self.ser.close()

# ================= DATA =================
LINES = {
    "Line 1": ["PN1001","PN1002"],
    "Line 2": ["PN002"],
    "Line 3": ["PN003"],
    "Line 4": ["PN004"],
    "Line 5": ["PN005"],
}

SPEC = {
    "PN1001": {
        "L": {"lower": 9.5, "upper": 10.5, "center": 10.0},
        "Q": {"lower": 30,  "upper": 50,   "center": 40.0}
    },
    "PN1002": {
        "L": {"lower": 6.5, "upper": 8.5, "center": 7.0},
        "Q": {"lower": 10,  "upper": 50,   "center": 30.0}
    },
    "PN002": {
        "L": {"lower": 8.5, "upper": 10.0, "center": 9.0},
        "Q": {"lower": 9.0, "upper": 10.0, "center": 9.5}
    },
     "PN003": {
        "L": {"lower": 8.5, "upper": 10.0, "center": 9.0},
        "Q": {"lower": 9.0, "upper": 10.0, "center": 9.5}
    },
     "PN004": {
        "L": {"lower": 4.0, "upper": 5.0, "center": 6.0},
        "Q": {"lower": 9.0, "upper": 10.0, "center": 9.5}
    },
     "PN005": {
        "L": {"lower": 6.0, "upper": 7.5, "center": 9.0},
        "Q": {"lower": 2.0, "upper": 3.5, "center": 5.0}
    }  
}

WARNING_RATIO = 0.15  # 15%

# =============== MOCK RS232 ===============
# def read_lq_rs232():
#     return {
#         "Lx": round(random.uniform(9, 11), 3),
#         "Qx": round(random.uniform(25, 55), 2),
#         "Ly": round(random.uniform(9, 11), 3),
#         "Qy": round(random.uniform(25, 55), 2),
#         "Lz": round(random.uniform(9, 11), 3),
#         "Qz": round(random.uniform(25, 55), 2),
#     }

# def read_r_rs232():
#     return {
#         "Rx": round(random.uniform(0.1, 0.5), 3),
#         "Ry": round(random.uniform(0.1, 0.5), 3),
#         "Rz": round(random.uniform(0.1, 0.5), 3),
#     }

# =============== EVALUATION LOGIC ===============
def evaluate_value(value, lower, upper, center):
    if value < lower or value > upper:
        return "FAIL"

    span = upper - lower
    warn_low = lower + span * WARNING_RATIO
    warn_high = upper - span * WARNING_RATIO

    if value < warn_low or value > warn_high:
        return "WARNING"

    return "PASS"

def check_lq_quality(data, spec):
    results = []

    for axis in ["x", "y", "z"]:
        results.append(evaluate_value(
            data[f"L{axis}"],
            spec["L"]["lower"],
            spec["L"]["upper"],
            spec["L"]["center"]
        ))
        results.append(evaluate_value(
            data[f"Q{axis}"],
            spec["Q"]["lower"],
            spec["Q"]["upper"],
            spec["Q"]["center"]
        ))

    if "FAIL" in results:
        return "FAIL"
    if "WARNING" in results:
        return "WARNING"
    return "PASS"

# =============== PLOT ===================
def plot_lq(results, spec):
    idx = [r["No"] for r in results]

    for param in ["L", "Q"]:
        plt.figure(figsize=(10, 5))

        for axis in ["x", "y", "z"]:
            values = [r[f"{param}{axis}"] for r in results]
            plt.plot(idx, values, marker='o', label=f"{param}{axis}")

        plt.axhline(spec[param]["lower"], linestyle="--", label="Lower")
        plt.axhline(spec[param]["upper"], linestyle="--", label="Upper")
        plt.axhline(spec[param]["center"], linestyle="-.", label="Center")

        plt.title(f"{param} Distribution (125 samples)")
        plt.xlabel("Sample No")
        plt.ylabel(param)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# =============== MAIN WINDOW ===============
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LCR Production Test")
        self.resize(1200, 550)

        self.results = []

        # Widgets
        self.cb_line = QComboBox()
        self.cb_line.addItems(LINES.keys())

        self.cb_part = QComboBox()

        self.btn_search = QPushButton("Search")
        self.btn_lq = QPushButton("Start LQ")
        self.btn_r = QPushButton("Start R")
        self.btn_plot = QPushButton("Plot LQ")
        self.btn_finish = QPushButton("Finish")

        self.btn_r.setEnabled(False)
        self.btn_plot.setEnabled(False)
        self.btn_finish.setEnabled(False)

        self.table = QTableWidget(125, 11)
        self.table.setHorizontalHeaderLabels([
            "No",
            "Lx", "Qx", "Ly", "Qy", "Lz", "Qz",
            "Rx", "Ry", "Rz",
            "Status"
        ])

        # Layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Line"))
        top.addWidget(self.cb_line)
        top.addWidget(QLabel("Part"))
        top.addWidget(self.cb_part)
        top.addWidget(self.btn_search)
        top.addWidget(self.btn_lq)
        top.addWidget(self.btn_r)
        top.addWidget(self.btn_plot)
        top.addWidget(self.btn_finish)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # Signals
        self.btn_search.clicked.connect(self.load_part)
        self.btn_lq.clicked.connect(self.measure_lq)
        self.btn_r.clicked.connect(self.measure_r)
        self.btn_plot.clicked.connect(self.plot)
        self.btn_finish.clicked.connect(self.save_csv)

    def load_part(self):
        line = self.cb_line.currentText()
        self.cb_part.clear()
        self.cb_part.addItems(LINES[line])

    # def measure_lq(self):
    #     part = self.cb_part.currentText()
    #     spec = SPEC[part]

    #     self.results.clear()
    #     self.table.clearContents()

    #     for i in range(125):
    #         lq = read_lq_rs232()
    #         status = check_lq_quality(lq, spec)

    #         record = {
    #             "No": i + 1,
    #             **lq,
    #             "Rx": None, "Ry": None, "Rz": None,
    #             "Status": status
    #         }
    #         self.results.append(record)
    #         self.update_row(i, record)

    #     self.btn_r.setEnabled(True)
    #     self.btn_plot.setEnabled(True)
    #     QMessageBox.information(self, "Done", "Đã đo xong L & Q")

    def measure_lq(self):
        part = self.cb_part.currentText()
        spec = SPEC[part]

        self.results.clear()
        self.table.clearContents()

        self.lcr.send(":MEAS:FUNC1 L")
        self.lcr.send(":MEAS:FUNC2 Q")
        self.lcr.setup_LQ()

        for i in range(125):
            Lx, Qx = self.lcr.measure_LQ()
            Ly, Qy = self.lcr.measure_LQ()
            Lz, Qz = self.lcr.measure_LQ()

            lq = {
            "Lx": Lx, "Qx": Qx,
            "Ly": Ly, "Qy": Qy,
            "Lz": Lz, "Qz": Qz,
            }

            status = check_lq_quality(lq, spec)

            record = {
            "No": i + 1,
            **lq,
            "Rx": None, "Ry": None, "Rz": None,
            "Status": status
            }

            self.results.append(record)
            self.update_row(i, record)

        self.btn_r.setEnabled(True)
        self.btn_plot.setEnabled(True)
        QMessageBox.information(self, "Done", "Đã đo xong L & Q")


    # def measure_r(self):
    #     for i in range(125):
    #         r = read_r_rs232()
    #         self.results[i]["Rx"] = r["Rx"]
    #         self.results[i]["Ry"] = r["Ry"]
    #         self.results[i]["Rz"] = r["Rz"]
    #         self.update_row(i, self.results[i])

    #     self.btn_finish.setEnabled(True)
    #     QMessageBox.information(self, "Done", "Đã đo xong R")
    def measure_r(self):
        self.lcr.setup_R()

        for i in range(125):
            Rx = self.lcr.measure_R()
            Ry = self.lcr.measure_R()
            Rz = self.lcr.measure_R()

            self.results[i]["Rx"] = Rx
            self.results[i]["Ry"] = Ry
            self.results[i]["Rz"] = Rz

            self.update_row(i, self.results[i])

        self.btn_finish.setEnabled(True)
        QMessageBox.information(self, "Done", "Đã đo xong R")


    def plot(self):
        plot_lq(self.results, SPEC[self.cb_part.currentText()])

    def update_row(self, row, data):
        keys = [
            "No", "Lx", "Qx", "Ly", "Qy", "Lz", "Qz",
            "Rx", "Ry", "Rz", "Status"
        ]
        for col, key in enumerate(keys):
            val = "" if data[key] is None else str(data[key])
            self.table.setItem(row, col, QTableWidgetItem(val))

    def save_csv(self):
        with open("result.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.table.horizontalHeaderItem(i).text()
                             for i in range(self.table.columnCount()))
            for r in self.results:
                writer.writerow([
                    r["No"],
                    r["Lx"], r["Qx"], r["Ly"], r["Qy"], r["Lz"], r["Qz"],
                    r["Rx"], r["Ry"], r["Rz"],
                    r["Status"]
                ])

        QMessageBox.information(self, "Saved", "Đã lưu result.csv")

# =============== RUN =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

    self.lcr = WayneKerrRS232(port="COM3")
