# Hướng dẫn sử dụng autograder

Tài liệu này giúp bạn (đặc biệt là sinh viên chưa quen cài Python) chạy giao diện `grade_ui.py` một cách nhanh nhất trên Windows.

## 1. Chuẩn bị
- Windows 10/11 64-bit.
- Java JDK 8+ (để chấm bài Java). Nếu chưa có, tải tại https://java.com/ và cài, sau đó đặt biến môi trường `JAVA_HOME` (không bắt buộc nhưng nên làm).
- Kết nối Internet để tải Python.

## 2. Cài Python nhanh
1. Vào https://www.python.org/downloads/windows/ và chọn **Download Python 3.x (64-bit)**.
2. Chạy file `.exe` vừa tải, **tích “Add Python 3.x to PATH”** ở màn hình đầu rồi bấm *Install Now*.
3. Sau khi cài xong, nhấn *Close*.
4. Mở Command Prompt (Win + R → `cmd`) và kiểm tra: `python --version`. Nếu hiển thị `Python 3.x`, bạn đã sẵn sàng.

> Nếu không muốn cài vào hệ thống, bạn có thể dùng bản portable: tải `python-3.xx-embed-amd64.zip`, giải nén vào thư mục bất kỳ rồi chạy `python.exe grade_ui.py`. Với cách này bạn phải tự chỉ rõ đường dẫn tới `python.exe` mỗi lần chạy.

## 3. Tải và chạy autograder
1. Tải mã nguồn (hoặc nhận từ giảng viên) và giải nén vào thư mục không dấu, ví dụ `C:\Autograder`.
2. Mở Command Prompt tại thư mục vừa giải nén (Shift + chuột phải → *Open PowerShell window here* hoặc gõ `cmd` trên thanh địa chỉ).
3. Chạy lệnh:
   ```bash
   python grade_ui.py
   ```
   Giao diện chấm bài sẽ mở lên.

## 4. Sử dụng giao diện
1. Nhấn **Chọn...** để trỏ tới thư mục gốc chứa `Q1`, `Q2`, … hoặc **Chọn ZIP...** nếu có file `.zip`.
2. (Tuỳ chọn) nhập `JAVA_HOME` nếu JDK không nằm trong `PATH`.
3. Điều chỉnh các thiết lập mặc định (Strict compare, bỏ khoảng trắng cuối dòng, v.v.) nếu cần.
4. Bấm **Chấm bài** để chạy chấm tự động.
5. Xem kết quả ở tab **Kết quả đơn lẻ** hoặc dùng các nút **Chấm hàng loạt...** / **Chấm nhiều ZIP...** cho các tình huống tương ứng.

## 5. Sự cố thường gặp
- **`python` không được nhận diện**: mở Command Prompt mới sau khi cài hoặc cài lại và nhớ tích “Add Python to PATH”.
- **Không tìm thấy `javac`/`java`**: kiểm tra JDK đã cài chưa; cập nhật `JAVA_HOME` hoặc thêm thư mục `bin` của JDK vào `PATH`.
- **Giao diện không mở**: chắc chắn bạn đang dùng Python 3.10+ (Tkinter có sẵn). Nếu dùng bản portable, giữ nguyên file `python311.zip` nằm cạnh `python.exe`.

Chúc bạn chấm bài thuận lợi!
