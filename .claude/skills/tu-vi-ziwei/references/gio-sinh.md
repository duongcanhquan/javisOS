# Giờ sinh → giờ chi (địa chi)

Dùng khi user đưa giờ đồng hồ. Script `lap-la-so.mjs` đã đổi tự động; bảng này để hỏi/xác nhận.

| Chi (branch) | Tên | Khoảng giờ |
|--------------|-----|------------|
| 0 | Tý (子) | 23:00 - 00:59 |
| 1 | Sửu (丑) | 01:00 - 02:59 |
| 2 | Dần (寅) | 03:00 - 04:59 |
| 3 | Mão (卯) | 05:00 - 06:59 |
| 4 | Thìn (辰) | 07:00 - 08:59 |
| 5 | Tỵ (巳) | 09:00 - 10:59 |
| 6 | Ngọ (午) | 11:00 - 12:59 |
| 7 | Mùi (未) | 13:00 - 14:59 |
| 8 | Thân (申) | 15:00 - 16:59 |
| 9 | Dậu (酉) | 17:00 - 18:59 |
| 10 | Tuất (戌) | 19:00 - 20:59 |
| 11 | Hợi (亥) | 21:00 - 22:59 |

Ghi chú:

- Sinh **23:00-23:59** thuộc Tý và thường đổi ngày âm theo quy tắc lập lá (iztro `bySolar` xử lý); nếu user thắc mắc, giải thích ngắn bằng kết quả `lunarDate` trên JSON.
- Không biết giờ: nêu giả định (ví dụ Ngọ) và đánh dấu lá số mang tính tham khảo.
