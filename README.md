# ⛑️ PPE Guardian — Hệ Thống Giám Sát Bảo Hộ Lao Động

Ứng dụng desktop Python phát hiện PPE theo thời gian thực bằng YOLOv8, giao diện PyQt6, lưu trữ MySQL, cảnh báo Telegram.

---

## 📁 Cấu Trúc Project

```
ppe_guardian/
├── main.py                  ← Điểm chạy chính
├── requirements.txt
├── setup_database.sql       ← Script tạo MySQL DB
├── app_config.json          ← Cấu hình tự động tạo
├── best.pt                  ← ⚠️ File model của bạn (đặt vào đây)
├── captured_violations/     ← Ảnh vi phạm được lưu tự động
├── core/
│   ├── detector.py          ← Engine YOLOv8
│   ├── database.py          ← MySQL manager
│   ├── telegram_alert.py    ← Gửi cảnh báo Telegram
│   ├── capture.py           ← Lưu ảnh vi phạm
│   └── config_manager.py    ← Quản lý cấu hình
└── ui/
    ├── main_window.py       ← Cửa sổ chính + sidebar
    ├── styles.py            ← Dark theme CSS
    └── pages/
        ├── dashboard.py     ← Tổng quan + stats
        ├── live_detection.py← Camera/video/ảnh
        ├── violations.py    ← Lịch sử + lọc + xuất CSV
        ├── statistics.py    ← Biểu đồ matplotlib
        └── settings.py      ← Cấu hình DB + Telegram + Model
```

---

## 🚀 Hướng Dẫn Cài Đặt

### Bước 1: Chuẩn bị môi trường Python

```bash
# Mở Command Prompt (cmd) hoặc PowerShell
# Tạo virtual environment
python -m venv venv

# Kích hoạt venv (Windows)
venv\Scripts\activate

# Cài thư viện
pip install -r requirements.txt
```

> ⏳ Việc cài `ultralytics` + `PyQt6` mất 5-10 phút, hãy chờ.

---

### Bước 2: Cài đặt MySQL

1. Tải **XAMPP**: https://www.apachefriends.org/  
   *hoặc* **MySQL Community**: https://dev.mysql.com/downloads/installer/

2. Khởi động MySQL Server (trong XAMPP → Start MySQL)

3. Mở **MySQL Workbench** hoặc **phpMyAdmin** (http://localhost/phpmyadmin)

4. Chạy file SQL:
   - Mở file `setup_database.sql`
   - Copy toàn bộ nội dung → Paste vào query editor → Chạy
   - Hoặc dùng command line:
   ```bash
   mysql -u root -p < setup_database.sql
   ```

---

### Bước 3: Đặt file model

```
Sao chép file best.pt vào thư mục ppe_guardian/
(cùng cấp với main.py)
```

---

### Bước 4: Tạo Telegram Bot (để nhận cảnh báo)

1. **Mở Telegram** → Tìm kiếm `@BotFather`
2. Gửi lệnh: `/newbot`
3. Đặt tên bot (vd: `PPE Guardian Bot`)
4. Đặt username (phải kết thúc bằng `bot`, vd: `ppe_guardian_mybot`)
5. **Copy Bot Token** được cấp (dạng: `123456789:ABCdefGHI...`)

6. **Lấy Chat ID:**
   - Tìm kiếm `@userinfobot` trên Telegram
   - Gửi `/start` → Bot sẽ trả về ID của bạn
   - **Hoặc** tìm kiếm `@RawDataBot` → gửi bất kỳ tin → lấy `"id"` trong JSON

7. **Quan trọng:** Gửi bất kỳ tin nhắn nào cho bot của bạn trước (tìm bot theo username → gửi `/start`)

8. Nhập Token + Chat ID vào app: **Settings → Telegram**

---

### Bước 5: Chạy ứng dụng

```bash
# Trong thư mục ppe_guardian/, với venv đã active
python main.py
```

---

## ⚙️ Cấu Hình Lần Đầu

Khi app mở lần đầu:

1. **Settings → Database**: Nhập host/user/password MySQL → Test → Lưu
2. **Settings → Telegram**: Nhập Token + Chat ID → Gửi test → Lưu  
3. **Settings → Model**: Xác nhận đường dẫn `best.pt` → Lưu

---

## 📱 Các Tính Năng

| Trang | Chức năng |
|-------|-----------|
| **Dashboard** | Tổng quan: số vi phạm hôm nay, tuần, tỷ lệ tuân thủ, vi phạm gần nhất |
| **Live Detection** | Webcam / file video / ảnh, hiển thị bounding box, nhãn, confidence |
| **Vi Phạm** | Lọc theo ngày & loại, phân trang, xuất CSV |
| **Thống Kê** | Biểu đồ đường (timeline), bánh (phân bố), cột ngang (top vi phạm) |
| **Cài Đặt** | DB, Telegram, model path, ngưỡng confidence, thư mục lưu ảnh |

---

## 🎯 14 Classes Được Phát Hiện

| Class | Ý nghĩa | Vi phạm? |
|-------|---------|---------|
| Hardhat | Đội mũ bảo hộ | ❌ |
| NO-Hardhat | Không đội mũ | ✅ |
| Mask | Đeo khẩu trang | ❌ |
| NO-Mask | Không đeo khẩu trang | ✅ |
| Gloves | Đeo găng tay | ❌ |
| NO-Gloves | Không đeo găng tay | ✅ |
| Goggles | Đeo kính bảo hộ | ❌ |
| NO-Goggles | Không đeo kính | ✅ |
| Safety Vest | Mặc áo phản quang | ❌ |
| NO-Safety Vest | Không mặc áo | ✅ |
| Fall-Detected | Phát hiện ngã/tai nạn | ✅🚨 |
| Person | Người | ❌ |
| Ladder | Thang | ❌ |
| Safety Cone | Cột chắn | ❌ |

---

## ❓ Xử Lý Sự Cố

**App báo "Không tải được model":**
→ Kiểm tra file `best.pt` có đúng thư mục chưa  
→ Settings → Model → duyệt chọn lại file

**Không kết nối MySQL:**
→ Kiểm tra MySQL Server đang chạy (XAMPP → MySQL → Start)  
→ Kiểm tra host/user/password trong Settings  

**Telegram không nhận được tin:**
→ Đảm bảo bạn đã gửi `/start` cho bot trước  
→ Kiểm tra Chat ID chính xác (không có dấu cách)  

**Webcam không mở được:**
→ Thử đổi index camera (mặc định 0, nếu có nhiều camera thử 1, 2...)  
→ Đóng các app khác đang dùng camera  

---

## 📋 Yêu Cầu Hệ Thống

- Windows 10/11 (64-bit)
- Python 3.10 hoặc 3.11
- RAM: tối thiểu 4GB (khuyến nghị 8GB)
- CPU: Intel Core i5 trở lên (không cần GPU)
- Ổ cứng: ~2GB cho dependencies
- MySQL 5.7+ hoặc MariaDB 10.4+
