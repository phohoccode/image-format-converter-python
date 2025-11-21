# 🖼️ Image Format Converter

Công cụ chuyển đổi định dạng ảnh từ URL sang các định dạng khác nhau bằng Python với giao diện terminal thân thiện và progress bar đẹp mắt.

## ✨ Tính năng

- ✅ Chuyển đổi ảnh từ một URL
- ✅ Chuyển đổi hàng loạt từ file chứa danh sách URL
- ✅ **Chuyển đổi từ file JSON (movies format)** - Tự động đọc `slug` làm tên file, `poster` làm URL
- ✅ **Progress bar thời gian thực** với tqdm - Hiển thị tiến độ, tốc độ, ETA
- ✅ Hỗ trợ 8 định dạng: PNG, JPEG, JPG, WEBP, BMP, GIF, TIFF, ICO
- ✅ Tùy chỉnh tên file đầu ra
- ✅ Chọn thư mục lưu ảnh tùy ý
- ✅ Xử lý tự động transparency cho JPEG
- ✅ **Nén WEBP tối ưu** - Quality 80%, method 6 cho kích thước nhỏ nhất
- ✅ **So sánh dung lượng** trước và sau khi chuyển đổi
- ✅ **Thống kê chi tiết** - Thành công, thất bại, bỏ qua

## 📋 Yêu cầu

```bash
pip install pillow requests tqdm
```

## 🚀 Cách sử dụng

### Chạy chương trình

```bash
python main.py
```

### Menu chính

```text
============================================================
🖼️  IMAGE FORMAT CONVERTER
============================================================
1. Chuyển đổi từ một URL
2. Chuyển đổi từ file chứa danh sách URL
3. Chuyển đổi từ file JSON (movies format)
4. Thoát
============================================================
```

### 1. Chuyển đổi từ một URL

Phù hợp cho việc chuyển đổi 1 ảnh đơn lẻ.

**Các bước:**

- Nhập URL ảnh
- Chọn định dạng đầu ra (1-8)
- Nhập đường dẫn thư mục lưu file
- Tùy chọn: Nhập tên file tùy chỉnh

**Ví dụ:**

```text
URL: https://example.com/image.png
Định dạng: 4 (WEBP)
Thư mục: ./output
Tên file: my-image (hoặc Enter để tự động)

✅ Kết quả: Hiển thị dung lượng file gốc và sau chuyển đổi, % tiết kiệm
```

### 2. Chuyển đổi từ file chứa URL

Phù hợp cho việc chuyển đổi nhiều ảnh từ các URL khác nhau.

**Tạo file `urls.txt`:**

```text
https://example.com/image1.png
https://example.com/image2.jpg
https://example.com/image3.webp
# Dòng bắt đầu bằng # sẽ bị bỏ qua
https://example.com/image4.png
```

**Các bước:**

- Chọn option 2 trong menu
- Nhập đường dẫn file: `urls.txt`
- Chọn định dạng đầu ra
- Nhập thư mục lưu file

**Kết quả:**

```text
🔄 Đang chuyển đổi: 100%|████████████| 4/4 [00:05<00:00, 0.75ảnh/s]

📊 KẾT QUẢ:
   ✅ Thành công: 4
   ❌ Thất bại: 0
   📊 Tổng cộng: 4
```

### 3. Chuyển đổi từ file JSON (Movies format) ⭐ MỚI

Phù hợp cho việc chuyển đổi hàng loạt poster phim từ file JSON.

**Format JSON yêu cầu:**

```json
[
  {
    "slug": "avatar-the-way-of-water",
    "poster": "https://phimimg.com/upload/vod/avatar.jpg"
  },
  {
    "slug": "top-gun-maverick",
    "poster": "https://phimimg.com/upload/vod/topgun.jpg"
  }
]
```

**Các bước:**

- Chọn option 3 trong menu
- Nhập đường dẫn file: `movies.json`
- Chọn định dạng đầu ra (khuyến nghị WEBP cho web)
- Nhập thư mục lưu file: `./posters`

**Kết quả:**

```text
🎬 Đang chuyển đổi poster: 100%|████████| 2/2 [00:03<00:00, 0.67phim/s]

📊 KẾT QUẢ:
   ✅ Thành công: 2
   ❌ Thất bại: 0
   ⏭️  Bỏ qua: 0
   📊 Tổng cộng: 2
```

**Đặc điểm:**

- File đầu ra tự động lấy tên từ trường `slug`: `avatar-the-way-of-water.webp`
- URL lấy từ trường `poster`
- Tự động bỏ qua các bản ghi thiếu `slug` hoặc `poster`
- Progress bar màu xanh với đơn vị "phim"
- Silent mode để không làm rối progress bar

## 📝 Định dạng được hỗ trợ

| Định dạng | Mô tả                            | Ghi chú                            |
| --------- | -------------------------------- | ---------------------------------- |
| PNG       | Portable Network Graphics        | Hỗ trợ transparency                |
| JPEG/JPG  | Joint Photographic Experts Group | Không hỗ trợ transparency          |
| WEBP      | Web Picture format               | Định dạng hiện đại, kích thước nhỏ |
| BMP       | Bitmap                           | Định dạng cơ bản                   |
| GIF       | Graphics Interchange Format      | Hỗ trợ animation                   |
| TIFF      | Tagged Image File Format         | Chất lượng cao                     |
| ICO       | Icon format                      | Dùng cho icon                      |

## 🎯 Ví dụ sử dụng

### Chuyển đổi một ảnh PNG sang JPEG

```
Chọn: 1
URL: https://picsum.photos/800/600
Định dạng: 2 (JPEG)
Thư mục: ./converted
Tên file: sample-image
```

### Chuyển đổi hàng loạt sang WEBP

```
Chọn: 2
File: urls.txt
Định dạng: 4 (WEBP)
Thư mục: ./webp-output
```

## ⚙️ Tính năng kỹ thuật

- **Tự động xử lý transparency**: Khi chuyển sang JPEG, tự động thêm nền trắng cho ảnh có alpha channel
- **Tối ưu hóa nén**:
  - JPEG: Quality 85%, optimize=True
  - PNG: optimize=True
  - WEBP: Quality 80%, method=6 (nén tốt nhất), optimize=True
- **Progress bar với tqdm**: Hiển thị tiến độ, tốc độ (ảnh/s hoặc phim/s), ETA
- **Silent mode**: Tắt log chi tiết khi xử lý hàng loạt để progress bar đẹp hơn
- **Xử lý lỗi thông minh**: Bắt lỗi và thông báo chi tiết, tự động bỏ qua lỗi và tiếp tục
- **User-Agent**: Sử dụng User-Agent để tránh bị chặn khi tải ảnh
- **Timeout**: Giới hạn thời gian tải ảnh là 30 giây
- **So sánh dung lượng**: Hiển thị % tăng/giảm dung lượng sau chuyển đổi

## 🐛 Xử lý lỗi

Chương trình sẽ thông báo chi tiết khi gặp lỗi:

- ❌ Lỗi kết nối hoặc URL không hợp lệ
- ❌ Lỗi khi xử lý ảnh (format không hỗ trợ)
- ❌ Lỗi khi tạo thư mục hoặc lưu file
- ❌ File URL không tồn tại hoặc không đọc được

## 📦 Cấu trúc thư mục

```text
image-format-converter/
├── main.py              # File chính chứa toàn bộ logic
├── README.md            # Hướng dẫn sử dụng chi tiết
├── requirements.txt     # Danh sách thư viện cần thiết
├── urls-sample.txt             # File mẫu chứa danh sách URL
├── movies.json          # File JSON chứa dữ liệu phim (nếu có)
└── movies-sample.json   # File JSON mẫu để test
```

## 📊 Ví dụ thực tế

### Chuyển đổi 25,000 poster phim sang WEBP

```text
📋 Tìm thấy 25298 bộ phim trong file
🎬 Đang chuyển đổi poster: 100%|████████| 25298/25298 [02:25:11<00:00, 2.90phim/s]

📊 KẾT QUẢ:
   ✅ Thành công: 24850
   ❌ Thất bại: 138 (URL không tồn tại hoặc hết hạn)
   ⏭️  Bỏ qua: 310 (thiếu slug hoặc poster)
   📊 Tổng cộng: 25298

⏱️  Thời gian: ~2.5 giờ
💾 Dung lượng: Trung bình giảm 35% so với JPG gốc
```

## 💡 Tips & Best Practices

1. **Chuyển đổi sang WEBP** - Khuyến nghị cho web hiện đại:

   - Kích thước nhỏ hơn 25-35% so với JPEG cùng chất lượng
   - Hỗ trợ transparency như PNG
   - Được hỗ trợ rộng rãi trên các trình duyệt hiện đại

2. **Chuyển đổi sang JPEG** - Khi cần tương thích rộng:

   - Phù hợp cho ảnh không có transparency
   - Kích thước nhỏ, tải nhanh
   - Hỗ trợ mọi trình duyệt và thiết bị

3. **Chuyển đổi sang PNG** - Khi cần chất lượng cao:

   - Giữ được transparency hoàn hảo
   - Không mất chất lượng (lossless)
   - Phù hợp cho logo, icon, graphics

4. **Sử dụng file JSON** (option 3) cho projects lớn:

   - Xử lý hàng ngàn poster cùng lúc
   - Tên file tự động từ slug, dễ quản lý
   - Progress bar giúp theo dõi tiến độ

5. **Tips khác**:
   - Thêm **#** ở đầu dòng trong file URL để comment
   - Tạo thư mục riêng cho từng định dạng: `./webp`, `./jpeg`
   - Kiểm tra kết quả với vài ảnh trước khi xử lý hàng loạt

## 🚀 Performance

- **Tốc độ**: ~1-2 ảnh/giây (tùy kích thước và kết nối)
- **WEBP method 6**: Chậm hơn nhưng nén tốt hơn 10-15%
- **Batch processing**: Xử lý tuần tự, ổn định với hàng ngàn ảnh
- **Memory efficient**: Xử lý từng ảnh một, không tốn RAM

## 📄 License

MIT License
