# Economy & Stat Balance Reference — v3.5.6

## Linh thạch

- Nhân vật mới bắt đầu với **1.000 linh thạch**.
- Chợ người chơi: người bán nhận **98%**, thuế **2%**. Chuyển trực tiếp không thu thuế.
- Gacha: **1.000 linh thạch** hoặc một Thiên Cơ Lệnh.
- Sáng lập tông môn: **10.000 linh thạch**.
- Điểm danh: `500 + min(streak, 30) × 50 + realm_index × 100`. Streak hiển thị vẫn tiếp tục, phần thưởng không tăng vô hạn.
- Chiến thắng: **20–80** linh thạch cơ bản; tinh anh ×**1,5**; boss ×**2**; phần thưởng còn nhân hệ số cảnh giới tối đa **1,65×**.
- Thất bại khi chiến đấu: mất **1% linh thạch** hiện có, **2% tu vi** hiện tại và nhận thương thế theo cảnh giới; phần mất không thể khiến tiền/tư vi âm.
- Thưởng linh thạch từ khám phá chịu ảnh hưởng May Mắn, tối đa **+25%**.

## Tu vi

- Tu luyện thông thường có cooldown **25 giây**.
- Khám phá có cooldown **90 giây**; săn có cooldown mở trận **75 giây**.
- Tu vi nhận từ đan dược, khám phá, chiến đấu, nhiệm vụ, sự kiện thế giới và bí cảnh được giới hạn ở ngưỡng của tầng hiện tại. Phần vượt ngưỡng không được tích trữ để bỏ qua nhiều lần đột phá.
- Bí cảnh vẫn có chu kỳ **3 giờ**; tu vi thưởng không vượt ngưỡng tầng, linh thạch vẫn nhận đầy đủ.

## Chỉ số nhân vật

- Nhân vật mới: từng chỉ số căn cơ/ngộ tính/may mắn/mệnh số/đạo tâm được tạo ngẫu nhiên trong **35–75**; nhân vật cũ không bị giảm chỉ số.
- Chỉ số cơ bản có hard cap **100**; khi dùng vật phẩm tăng chỉ số vĩnh viễn, từ 60 hiệu suất tăng bị giảm một nửa, từ 80 giảm còn một phần ba. Một số hiệu ứng nhiệm vụ áp dụng delta nhỏ trực tiếp nhưng vẫn bị chặn ở hard cap 100.
- Phần tăng chỉ số vĩnh viễn từ cùng một loại vật phẩm chỉ áp dụng một lần mỗi nhân vật. Nếu vật phẩm đồng thời có tu vi/HP, các hiệu ứng lặp lại đó vẫn dùng được; chỉ số vĩnh viễn không cộng lần nữa.

## Đột phá

Tỷ lệ hiện dùng: `0,25 + căn_cơ×0,0025 + đạo_tâm×0,002 + ngộ_tính×0,0015 + đạo_giai×0,02 + bonus_chuẩn_bị − thương_thế×0,01`, giới hạn trong **5%–90%**. Bonus từ vật phẩm và hệ thống chuẩn bị vẫn được áp dụng theo quy tắc hiện có.

## Trang bị / kỹ năng

- Vũ khí: tối đa **40 công** trên một món trong catalog hiện tại.
- Trang bị: tối đa **32 thủ** (Kim Cang Giáp) và **22 HP** cộng thêm (Huyền Vũ Giáp) trên một món trong catalog hiện tại.
- Kháng lôi trên một món trang bị không quá **10%**; mô tả trong shop phải khớp giá trị thực.
- Công pháp: hệ số sức mạnh kỹ năng tối đa trong catalog là **×1,25**; mastery tăng sát thương tối đa **12%**.
- Công thức chiến đấu: sát thương cơ bản dùng `max(1, công − thủ × 0,55)` với dao động ±12%; tỷ lệ đánh trúng được giới hạn **35%–97%**; tỷ lệ chí mạng tối đa **50%**.
- HP thực chiến là HP cơ bản cộng trang bị rồi nhân hiệu ứng Đạo/thiên phú; menu và trang nhân vật dùng cùng phép tính với chiến đấu. Đổi/tháo trang bị sẽ kẹp HP hiện tại theo giới hạn thực chiến mới.

## Lưu ý vận hành

Đây là bảng cân bằng gameplay, không thay thế kiểm thử thực chiến. Các thay đổi ảnh hưởng hành vi của phần thưởng nhưng không yêu cầu migration database. Nhân vật cũ giữ nguyên chỉ số và streak; những chỉ số đã nhận từ item trước bản này không thể tự động hoàn nguyên an toàn.
