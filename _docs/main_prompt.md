Tôi muốn tạo một ứng dụng Python độc lập (standalone) để chuyển đổi file video từ định dạng .ts sang .mp4.

**Yêu cầu chức năng:**

1. **Giao diện đồ họa (GUI):**
   - Sử dụng thư viện GUI phù hợp cho Windows (ví dụ: tkinter, PyQt, hoặc tương tự)
   - Hỗ trợ kéo thả (drag & drop) nhiều file .ts cùng lúc vào cửa sổ ứng dụng, hoặc import file bằng button
   - Giao diện thân thiện, dễ sử dụng

2. **Tùy chọn lưu file đầu ra:**
   - Cho phép người dùng chọn thư mục đích để lưu file .mp4
   - Hoặc mặc định lưu file .mp4 cùng thư mục với file .ts gốc
   - Giữ nguyên tên file, chỉ thay đổi phần mở rộng từ .ts sang .mp4

3. **Hiển thị tiến trình:**
   - Danh sách tất cả file .ts đã được thêm vào (hiển thị tên file, đường dẫn)
   - Thanh tiến trình (progress bar) cho từng file đang được convert
   - Trạng thái của mỗi file: Đang chờ / Đang convert / Hoàn thành / Lỗi

4. **Phương pháp chuyển đổi:**
   - Sử dụng FFmpeg với lệnh remux (không re-encode): `ffmpeg -i input.ts -c copy -f mp4 output.mp4`
   - Phương pháp này chỉ đóng gói lại container, không encode lại video/audio nên:
     - Tốc độ rất nhanh
     - Sử dụng CPU tối thiểu
     - Không làm giảm chất lượng video

5. **Xử lý hàng loạt:**
   - Convert nhiều file theo hàng đợi (queue)
   - Xử lý tuần tự từng file một (không convert song song để tránh quá tải)
   - Cho phép thêm/xóa file khỏi hàng đợi trước khi bắt đầu

6. **Chức năng bổ sung (nếu khả thi):**
   - Preview/xem trước file .ts trước khi convert (sử dụng video player nhúng hoặc mở bằng player mặc định)

**Yêu cầu kỹ thuật:**

- Ngôn ngữ: Python 3.x
- Đóng gói thành file .exe hoặc .pyz để chạy độc lập trên Windows (không cần cài đặt Python)
- FFmpeg: Có thể đóng gói kèm hoặc hướng dẫn người dùng cài đặt
- Xử lý lỗi: Thông báo rõ ràng khi file không hợp lệ hoặc FFmpeg gặp lỗi

**Lưu ý về code mẫu:**
Code sau đây là tham khảo cách sử dụng FFmpeg, KHÔNG THAY ĐỔI:
```
ffmpeg -i input.ts -c copy -f mp4 output.mp4
```

Hãy tạo cấu trúc dự án, thiết kế giao diện, và implement đầy đủ các chức năng trên.