# UI Design System — v3.6.3

## Visual direction

Kato Tu Tiên dùng phong cách **xianxia RPG HUD**: màu tím cho Đạo lực/tiến triển, xanh ngọc cho thành công, xanh thiên thanh cho hồ sơ, vàng linh khí cho kinh tế/cảnh báo và đỏ cho thao tác nguy hiểm. Các màn hình có author/footer chung; title và icon nhận diện rõ hệ thống.

## Layout patterns

- **Hub**: menu hệ thống dạng select ở đầu, 4–8 nút tắt cho khu vực được dùng thường xuyên, luôn có nút làm mới/đóng khi phù hợp.
- **Character HUD**: cảnh giới, Đạo lộ, linh thạch, HP, công/thủ, căn cơ/ngộ tính và thanh tiến độ tu vi.
- **Catalog / inventory**: chọn danh mục → chọn vật phẩm → panel chi tiết → hành động có kiểm soát. Danh sách kho đồ dùng 12 mục/trang để dễ đọc trên điện thoại.
- **Quest journal**: tổng quan, nhóm Khởi hành/Ngày/Tuần, tiến độ, thưởng và nhiệm vụ đang chọn.
- **World / secret realm**: mỗi khu/sự kiện có field riêng cho yêu cầu, phần thưởng, thời gian/tiến độ và rủi ro.
- **Combat HUD**: hai bảng đối thủ/tu sĩ, thanh HP, công/thủ, nhật ký diễn biến; chỉ trình bày kết quả từ encounter hiện tại.
- **Destructive/admin actions**: dùng style danger và vẫn phải giữ quyền kiểm tra ở callback/service.

## Platform compatibility

Bản này dùng embeds + Discord buttons/select menus chuẩn `discord.py` vì `requirements.txt` cho phép `discord.py>=2.3.0`. Select menus được giới hạn 25 option và nhãn/placeholder được cắt theo giới hạn API. Components V2 không được bật toàn cục để tránh yêu cầu nâng cấp dependency hoặc làm hỏng message cũ.

## Scope

Đợt rework chỉ chỉnh cấu trúc trình bày và cách chọn mục. Không đổi schema database, economy, công thức chỉ số hay callback/service chiến đấu.
