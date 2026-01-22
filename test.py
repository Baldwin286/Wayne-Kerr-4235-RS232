import serial
import time

# Cấu hình thông số RS232 theo Manual 
# Pinout: RxD (2), TxD (3), GND (5), RTS (7), CTS (8) [cite: 181]
try:
    ser = serial.Serial(
        port='COM7',        # Thay đổi số cổng COM cho đúng với máy tính của bạn
        baudrate=9600,      # Tốc độ cố định của máy 4300 [cite: 1821-1822]
        bytesize=serial.EIGHTBITS, # 8 bits dữ liệu [cite: 1823]
        parity=serial.PARITY_NONE, # Không có parity [cite: 1826-1827]
        stopbits=serial.STOPBITS_ONE, # 1 stop bit [cite: 1824-1825]
        timeout=2           # Đợi phản hồi trong 2 giây
    )
except Exception as e:
    print(f"Lỗi mở cổng COM: {e}")
    exit()

def send_command(cmd):
    """Gửi lệnh kèm ký tự kết thúc LF (\n) theo yêu cầu của máy """
    ser.write((cmd + '\n').encode('ascii'))
    time.sleep(0.2) # Đợi máy xử lý lệnh [cite: 1659]

def get_response():
    """Đọc dữ liệu phản hồi từ máy"""
    return ser.readline().decode('ascii').strip()

# --- BẮT ĐẦU KIỂM TRA ---

print("--- KIỂM TRA KẾT NỐI WAYNE KERR 4300 ---")

# 1. Truy vấn thông tin máy [cite: 1810]
send_command("*IDN?")
idn = get_response()
if idn:
    print(f"Kết nối thành công! Thiết bị: {idn}")
else:
    print("Không nhận được phản hồi. Kiểm tra cáp và cài đặt RS232 trên máy.")
    ser.close()
    exit()

# 2. Thiết lập cơ bản để thử nghiệm [cite: 1893, 2000]
send_command(":MEAS:FUNC1 L")    # Đo Inductance (L) [cite: 1999]
send_command(":MEAS:FUNC2 Q")    # Đo Quality Factor (Q) 
send_command(":MEAS:FREQ 1000")  # Tần số 1kHz [cite: 1952]
send_command(":MEAS:SPEED MED")  # Tốc độ Trung bình [cite: 1954]

print("\nBắt đầu lấy dữ liệu (Nhấn Ctrl+C để dừng)...")
print(f"{'L (H)':<20} | {'Q':<20}")
print("-" * 45)

try:
    while True:
        # Gửi lệnh Trigger và nhận kết quả ngay lập tức 
        send_command(":MEAS:TRIGger")
        data = get_response()
        
        if data:
            # Máy trả về định dạng: val1, val2 
            # Ví dụ: +1.234567E-06, +4.567890E-01
            print(data) 
        
        time.sleep(1) # Lấy dữ liệu mỗi giây 1 lần

except KeyboardInterrupt:
    print("\nĐã dừng thu thập dữ liệu.")
finally:
    ser.close()
    print("Đã đóng cổng COM.")