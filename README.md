# VINAMR AutoField — Hệ Thống Quản Lý & Báo Cáo Quota Tuyển Dụng Ô Tô

Hệ thống điều hành và trực quan hóa quota chuyên nghiệp dành cho **Công ty Nghiên cứu Thị trường**, phục vụ chiến dịch tuyển dụng đáp viên khảo sát xe ô tô toàn quốc (`Dự án 0747` & `Dự án 0748`).

---

## 🌟 Trải Nghiệm Giao Diện Mới (Executive Modern Dashboard)

Giao diện được tái thiết kế toàn diện theo phong cách **Executive Dark Glassmorphism** hiện đại:
* **Typography Đỉnh Cao**: Sử dụng font chữ cao cấp `Plus Jakarta Sans` kết hợp số liệu dạng `JetBrains Mono`.
* **Thanh Điều Hướng Thông Minh**:
  * Chuyển đổi nhanh 2 dự án `0747` và `0748` bằng nút bấm pill với hiệu ứng phát sáng.
  * Lựa chọn khu vực tức thì: `TP.HCM`, `Hà Nội`, `Đà Nẵng`, `Hải Phòng`, `Nghệ An`, `Cần Thơ`.
  * Bộ chọn ngày áp dụng quota linh hoạt.
* **4 Thẻ Chỉ Số KPI Trực Quan**:
  * **Tổng còn thiếu của thành phố**: Số lượng đáp viên cần tìm hôm nay.
  * **Số dòng xe mở tuyển**: Đang mở bao nhiêu mẫu xe, đã khóa bao nhiêu mẫu.
  * **Tiến độ hoàn thành**: Thanh tiến độ Gradient trực quan.
  * **Cảnh báo khống chế**: Số dòng xe bị chạm trần vùng miền hoặc trần hình thức mua.
* **Bảng Dữ Liệu Tương Tác Sống Động**:
  * Tìm kiếm nhanh mẫu xe theo thời gian thực (gõ đến đâu lọc đến đó).
  * Lọc xe theo từng phân khúc (`MINI/A-`, `B-SD`, `A SUV`, `B SUV`, `C-SUV`, `D-SUV`, `MPV`, `PICK-UP`).
  * Huy hiệu phân cấp màu sắc: `Nam` (Xanh dương đậm), `Nam / Nữ` (Tím), `Còn thiếu` (Xanh ngọc lục bảo), `Lưu ý khống chế` (Hổ phách cảnh báo).
* **Công Cụ Kiểm Tra Đáp Viên Hiện Trường (Instant Candidate Validator)**:
  * Điền nhanh: Mẫu xe + Tình trạng + Giới tính + Hình thức mua $\rightarrow$ Hệ thống lập tức trả kết quả: **HỢP LỆ (Còn bao nhiêu chỉ tiêu)** hoặc **TỪ CHỐI (Kèm lý do cụ thể: xe này đã đủ nữ, trần hình thức đã hết...)**.
* **Hộp Thoại Tải File Thông Minh (Modal Upload)**:
  * Kéo thả file XML / Excel trực tiếp, chọn ngày và dự án.
* **Xuất Báo Cáo 1-Click**:
  * Tải file **Excel (.xlsx)** định dạng chuẩn 2 sheet (*Dự định mua* & *Đã sở hữu*).
  * In ấn hoặc lưu file **PDF Báo Cáo** chuẩn mẫu trình bày.

---

## 🚀 Khởi Động Ứng Dụng Cục Bộ (Local)

### Cách 1: Click phím tắt (Dành cho Windows)
* Nhấp đúp chuột vào file: **`run_app.bat`** (hoặc chuột phải vào `run_app.ps1` chọn *Run with PowerShell*).

### Cách 2: Chạy bằng dòng lệnh
```powershell
& "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" server.py
```

Mở trình duyệt truy cập ngay:
👉 **http://localhost:8000** hoặc **http://127.0.0.1:8000**

---

## ☁️ Hướng Dẫn Đưa Lên Online (GitHub & Cloud Database)

### Bước 1: Đẩy mã nguồn lên GitHub
1. Mở trình duyệt vào [GitHub New Repo](https://github.com/new).
2. Đặt tên Repository (ví dụ: `vinamr-autofield`), chọn **Public** hoặc **Private**, và **không** tích chọn "Add a README file".
3. Nhấn **Create repository**.
4. Chạy 2 lệnh sau trong terminal để đẩy toàn bộ mã nguồn lên:
```powershell
git remote add origin https://github.com/Duytien2203/vinamr-autofield.git
git push -u origin main
```

---

### Bước 2: Thiết lập Database Online & Triển khai Web (Miễn phí)

#### Lựa chọn A (Khuyến nghị 1-Click): Triển khai trên Render.com
1. Đăng nhập [Render.com](https://render.com) bằng tài khoản GitHub của bạn.
2. Nhấn **New +** $\rightarrow$ chọn **Web Service**.
3. Chọn repo `vinamr-autofield` vừa đẩy lên.
4. Cấu hình cơ bản:
   * **Language / Environment**: `Python 3`
   * **Region**: `Singapore` (để tốc độ truy cập từ Việt Nam nhanh nhất)
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   * **Instance Type**: `Free`
5. **Cấu hình Database Online**:
   * **Cách 1 (Lưu ổ đĩa đám mây Persistent Disk)**: Tại mục *Disks*, chọn *Add Disk*: Name `vinamr-data`, Mount Path `/var/data`. Thêm biến môi trường (*Environment Variables*): `DB_PATH = /var/data/quota_system.db`.
   * **Cách 2 (Cloud PostgreSQL với Supabase / Neon)**: Tạo 1 database miễn phí tại [Neon.tech](https://neon.tech) hoặc [Supabase.com](https://supabase.com). Copy chuỗi kết nối dán vào biến môi trường: `DATABASE_URL = postgresql://...`. Hệ thống sẽ tự động tạo bảng và lưu trữ trên PostgreSQL.
6. Nhấn **Deploy Web Service**. Sau 1 - 2 phút, bạn sẽ nhận được một đường link web công khai dạng:
   👉 **`https://vinamr-autofield.onrender.com`**

#### Lựa chọn B: Triển khai trên Railway.app
1. Đăng nhập [Railway.app](https://railway.app) bằng GitHub.
2. Chọn **Deploy from GitHub repo** $\rightarrow$ chọn `vinamr-autofield`.
3. Bấm **+ New** $\rightarrow$ **Database** $\rightarrow$ **Add PostgreSQL**.
4. Railway sẽ tự động kết nối biến `DATABASE_URL` sang Web Service. Mọi upload quota sẽ được tự động đồng bộ vào Cloud Database.

---

## 📂 Cấu Trúc Dự Án

```
VINAMR Field/
├── server.py                  # Máy chủ Web & REST API tốc độ cao (Starlette + Uvicorn)
├── templates/
│   └── index.html             # Giao diện SPA hiện đại (Tailwind CSS + Alpine.js + Lucide)
├── core/
│   ├── parser.py              # Đọc file SpreadsheetML XML & Excel
│   ├── engine.py              # Bộ máy phân tích ràng buộc quota đa tầng
│   └── reporter.py            # Xuất báo cáo Excel (.xlsx) & HTML/PDF layout
├── database/
│   └── db.py                  # Cơ sở dữ liệu SQLite quản lý lịch sử upload theo ngày
├── data/
│   ├── quota_system.db        # File Database SQLite
│   ├── samples/               # File quota mẫu ngày 06/11/2026
│   └── uploads/               # Nơi lưu trữ các file quota tải lên hàng ngày
├── tests/
│   └── test_engine.py         # Kiểm thử tự động đối chiếu khớp 100% dữ liệu PDF
├── run_app.bat                # Phím tắt khởi động ứng dụng 1-click
├── run_app.ps1                # Script khởi động PowerShell
└── README.md
```

---

## 🧪 Kết Quả Đối Chiếu Quota TP.HCM (Ngày 06/11/2026)

* **Nhóm Dự Định Mua:** Đúng 4 dòng xe, tổng thiếu **4 đáp viên** (`VF3: 1`, `HR-V HEV: 1`, `Xforce: 1`, `CR-V: 1`).
* **Nhóm Đã Sở Hữu:** Đúng 22 dòng xe, tổng thiếu **134 đáp viên** (tính chuẩn trần miền Nam cho `Corolla Cross: 7`, trần hình thức cho `Territory: 5`, khóa nữ theo phân khúc cho `Raize` & `Sonet`).
