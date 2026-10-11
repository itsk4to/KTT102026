# Kato Tu Tiên UI Theme Tree

`ui/theme/` là design system dùng chung cho toàn bộ giao diện Discord. Nó chỉ xử lý presentation; không chứa gameplay rules, quyền quản trị, database hay logic giao dịch.

- `tokens.py`: bảng màu Đạo lực/Jade/Celestial/Gold/Danger, footer thương hiệu, timeout và vai trò nút theo ngữ nghĩa.
- `embeds.py`: factory embed thống nhất, màu theo loại màn hình, helper tạo panel/stat/progress.
- `components.py`: constructor nút và dropdown giới hạn kích thước đúng Discord, có xử lý lựa chọn rỗng.
- `views.py`: `ThemedView` chuẩn hóa kiểu màu/biểu tượng cho nút tạo sẵn và nút thêm động.

## Quy tắc giao diện

1. Mọi màn hình nên dùng `ui.embeds.base_embed()` (ủy quyền vào theme) thay vì tự tạo embed rời.
2. Dùng màu theo trạng thái: thành công/Jade, cảnh báo/Gold, lỗi/Đỏ, thông tin/Celestial, tiến triển/Đạo lực.
3. Trình bày số liệu quan trọng bằng field: trạng thái, giá/chi phí, chỉ số, tiến độ và hành động tiếp theo. Hạn chế đoạn văn dài.
4. Dùng dropdown để chọn một mục trong danh sách dài; dùng nút cho hành động nhanh/đã xác nhận. Chia trang nếu vượt giới hạn danh sách.
5. Theo giới hạn Discord, mỗi View có tối đa 5 hàng nút và mỗi select tối đa 25 lựa chọn. Nhãn nút tối đa 80 ký tự, placeholder tối đa 150 ký tự.
6. Mỗi view kế thừa `ThemedView`; giữ callback, quyền truy cập và xử lý dữ liệu ở module tính năng hiện tại.
7. Không thay logic gameplay chỉ để làm đẹp giao diện. Không đưa database/service vào theme.
8. Giữ timeout hữu hạn trừ khi đó là persistent view đã được thiết kế/đăng ký riêng.

## Thêm một GUI mới

Tạo file trong `ui/views/`, kế thừa `ThemedView`, dùng `base_embed()` và ưu tiên `themed_button()` / `themed_select()`. Thêm test cấu trúc và bảo đảm mọi callback có kiểm tra người thao tác.
