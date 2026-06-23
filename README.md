# VAL-CORE — Valorant True Stretched Launcher

**VAL-CORE** là một công cụ hỗ trợ giao diện đồ họa (GUI) mạnh mẽ được viết bằng Python, sử dụng thư viện `CustomTkinter`. Công cụ này giúp người chơi VALORANT cấu hình độ phân giải kéo giãn thực tế (True Stretched Resolution) một cách nhanh chóng và an toàn, tự động tối ưu hệ thống, đồng thời tích hợp các phần mềm hỗ trợ chơi game phổ biến.

---

## 🚀 Các Tính Năng Nổi Bật

### 1. Cấu hình True Stretched tự động
*   **Bỏ viền đen**: Tự động can thiệp và chỉnh sửa cấu trúc tệp cấu hình game `GameUserSettings.ini` của VALORANT, đưa game về chế độ Fullscreen Windowed phù hợp để hiển thị tỉ lệ kéo giãn mà không bị viền đen (black bars).
*   **Ép độ phân giải màn hình**: Sử dụng công cụ `QRes.exe` tích hợp hoặc Windows Native API để thay đổi độ phân giải toàn hệ thống thành độ phân giải stretched được chọn (ví dụ: `1280x960`, `1440x1080`, `1024x768`,...).
*   **Hỗ trợ Khôi phục (Rollback)**: Tự động khôi phục độ phân giải màn hình ban đầu (mặc định là `1920x1080`) ngay khi đóng game VALORANT hoặc tắt launcher.

### 2. Tối ưu hóa Hệ thống & Sửa lỗi
*   **Chế độ Aggressive (Ẩn Taskbar)**: Tự động ẩn thanh tác vụ Windows (Taskbar) khi khởi động game nhằm tránh tình trạng đè cửa sổ hoặc giật lag, sau đó hiển thị lại khi thoát game.
*   **Monitor Pulse (Reset màn hình)**: Sử dụng PowerShell để chu kỳ lại trạng thái màn hình (Disable/Enable PnP Monitor), giúp khắc phục triệt để lỗi viền đen màn hình trên Windows 11.
*   **CPU Priority Booster**: Nâng cấp độ ưu tiên xử lý của tiến trình VALORANT trong CPU lên mức **High Priority** nhằm tối ưu hóa FPS và giảm giật lag đột ngột.

### 3. Tích hợp Công cụ Hỗ trợ
*   **VibranceGUI**: Tự động bật VibranceGUI để tăng độ bão hòa màu sắc của game khi bắt đầu khởi chạy (tự động tắt nếu phát hiện chạy trên Laptop nhằm tránh lỗi xung đột card đồ họa onboard/rời).
*   **WO Mic Client**: Tự động kiểm tra cài đặt và khởi chạy Client WO Mic. Nếu chưa cài đặt, launcher sẽ chạy bộ cài đặt silent `/S` từ thư mục `bin`.

### 4. Giao diện Đồ họa Tương tác & Hiện đại
*   **Bảng điều khiển đa dạng**: Hỗ trợ 4 bố cục giao diện khác nhau có thể thay đổi trực tiếp:
    1.  *Elite Hybrid* (Mặc định - Thanh điều hướng bên trái)
    2.  *Top Nav Minimal* (Thanh điều hướng tối giản phía trên)
    3.  *All-in-One Dashboard* (Giao diện hiển thị toàn bộ dạng thẻ cuộn mượt mà)
    4.  *Glassmorphism Floating* (Hiệu ứng kính mờ lơ lửng độc đáo)
*   **Chủ đề màu sắc**: 4 chủ đề bắt mắt (*Elite Cyber*, *Neon Void*, *Toxicity*, *Retro Gold*) cùng hiệu ứng chuyển trang (Smooth Slide, Bounce, Elastic) và tốc độ hoạt ảnh có thể tùy chỉnh.
*   **Diagnostics Live**: Hiển thị trực tiếp các thông số hệ thống như: Quyền Admin, độ phân giải hiện tại, tình trạng tìm kiếm Riot Client, trạng thái bật/tắt các tool đi kèm.
*   **Log Console**: Ghi nhận toàn bộ quá trình khởi chạy, xử lý lỗi và tiến trình kết nối theo thời gian thực trực quan trên GUI.

---

## 🛠️ Yêu cầu Hệ thống

*   **Hệ điều hành**: Windows 10 hoặc Windows 11 (64-bit).
*   **Quyền hạn**: **Quyền Administrator** (Bắt buộc để thay đổi cài đặt hiển thị hệ thống, chỉnh sửa cấu hình game và tăng độ ưu tiên tiến trình CPU).
*   **Python**: Phiên bản `3.10` trở lên (nếu chạy từ mã nguồn).

---

## 📂 Cấu trúc Thư mục Dự án

```text
Valorant-True-Stretched/
├── assets/
│   └── valorant_logo.ico       # Icon chính của ứng dụng
├── bin/
│   ├── QRes.exe                # Công cụ dòng lệnh thay đổi độ phân giải màn hình nhanh
│   ├── vibranceGUI.exe         # Tiện ích tự động chỉnh độ bão hòa màu màn hình
│   └── womic_installer.exe     # Bộ cài đặt client WO Mic
├── dist/                       # Thư mục build (nếu có sau khi đóng gói pyinstaller)
├── Run.bat                     # File Batch script khởi chạy nhanh ứng dụng với quyền Admin
├── ValorantCore.py             # File mã nguồn Python chính chứa toàn bộ logic GUI & Core
└── requirements.txt            # Danh sách các thư viện Python cần cài đặt
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### Cách 1: Chạy trực tiếp từ mã nguồn Python

1.  **Cài đặt Python**: Tải và cài đặt [Python](https://www.python.org/downloads/) (Lưu ý tích chọn *Add Python to PATH* lúc cài đặt).
2.  **Cài đặt các thư viện yêu cầu**:
    Mở CMD hoặc PowerShell tại thư mục dự án và chạy lệnh sau:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Khởi chạy ứng dụng**:
    Nhấp đúp chuột vào tệp `Run.bat`.
    *Lưu ý:* File batch này được cấu hình sẵn để tự động phát hiện và yêu cầu bạn cấp quyền Administrator trước khi chạy tệp `ValorantCore.py`.

---

## ⚙️ Hướng dẫn Sử dụng trên GUI

1.  **Nhập Độ phân giải Stretched**: Trên tab **Dashboard**, nhập độ phân giải ngang (X) và dọc (Y) mong muốn (Ví dụ: `1280` x `960`) hoặc bấm chọn nhanh các Preset được tạo sẵn bên dưới.
2.  **Cài đặt nâng cao**: Sang tab **Core Engine** để bật/tắt các tính năng như *Monitor Pulse* (nếu dùng Win 11 bị viền đen), *CPU Priority Booster* (tăng FPS), hoặc chỉnh sửa đường dẫn cài đặt của Riot Client nếu launcher không tự phát hiện được.
3.  **Bật các công cụ đi kèm**: Sang tab **Settings** và kích hoạt *Auto-Launch VibranceGUI* hoặc *Auto-Launch WO Mic* nếu cần.
4.  **Bắt đầu chơi game**: Nhấp vào nút **▶ INJECT GAME** lớn ở góc dưới. Launcher sẽ thực hiện chuỗi lệnh:
    *   Thay đổi độ phân giải màn hình của bạn sang độ phân giải Stretched.
    *   Ẩn thanh Taskbar (nếu bật Aggressive Mode).
    *   Chạy các tool hỗ trợ đi kèm.
    *   Mở game VALORANT và giám sát tiến trình.
5.  **Sau khi chơi xong**: Chỉ cần tắt game VALORANT như bình thường. Launcher sẽ tự động phát hiện game đã đóng, khôi phục lại độ phân giải màn hình mặc định và hiển thị lại Taskbar của bạn. Nếu game bị đơ hoặc lỗi, bạn có thể bấm **ABORT ENGINE** trên giao diện launcher để cưỡng chế đóng game lập tức.

---

## 📝 Lưu ý Quan trọng

*   **Quyền Admin**: Không chạy trực tiếp tệp `ValorantCore.py` mà không mở CMD với quyền Admin hoặc không dùng `Run.bat`, vì ứng dụng sẽ báo lỗi thiếu quyền kiểm soát hệ thống và tự đóng.
*   **Tệp tin cấu hình**: Khi inject game, công cụ sẽ ghi đè thuộc tính chỉ đọc (Read-only) của tệp cấu hình VALORANT `GameUserSettings.ini` để tránh game tự động reset độ phân giải, sau đó khóa tệp tin lại dưới dạng Read-only.
*   **Bảo mật**: Các lệnh tắt/bật ứng dụng và khởi chạy game được gọi an toàn thông qua các mảng tham số (`subprocess.run` / `subprocess.Popen` không dùng `shell=True`) để ngăn chặn các lỗ hổng chèn lệnh (Command Injection).

---

*Phát triển và tối ưu bởi MinhYz.*
