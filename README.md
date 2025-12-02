# Image Format Converter

Công cụ chuyển đổi định dạng ảnh từ URL sang các định dạng khác nhau bằng Python với giao diện terminal hiện đại và đẹp mắt sử dụng Rich.

## Tính năng

- **Giao diện đẹp mắt** - Sử dụng Rich library với gradient colors, tables và panels
- Chuyển đổi ảnh từ một URL
- Chuyển đổi hàng loạt từ file chứa danh sách URL với đa luồng
- **Chuyển đổi từ file JSON (movies format)** - Tự động đọc `slug` làm tên file, `url` làm URL
- **Tự động phát hiện file JSON trong thư mục mock** - Hiển thị danh sách file có sẵn để chọn nhanh
- **Lọc phim chưa tải** - So sánh với thư mục ảnh, tạo danh sách phim cần tải
- **Xử lý đa luồng** - Hỗ trợ 1-20 luồng, tăng tốc 3-5 lần
- **Checkpoint/Resume** - Lưu tiến trình tự động, tiếp tục khi bị gián đoạn
- **Progress bar thời gian thực** với tqdm - Hiển thị tiến độ, tốc độ, ETA
- Hỗ trợ 8 định dạng: PNG, JPEG, JPG, WEBP, BMP, GIF, TIFF, ICO
- Tùy chỉnh tên file đầu ra
- Chọn thư mục lưu ảnh tùy ý
- Xử lý tự động transparency cho JPEG
- **Nén WEBP tối ưu** - Quality 80%, method 6 cho kích thước nhỏ nhất
- **So sánh dung lượng** trước và sau khi chuyển đổi
- **Thống kê chi tiết** - Thành công, thất bại, bỏ qua với bảng đẹp
- **Silent mode** - Không in log khi xử lý hàng loạt để progress bar đẹp hơn
- **Hướng dẫn tích hợp** - Menu hướng dẫn chi tiết ngay trong app

## Yêu cầu

```bash
pip install pillow requests tqdm rich
```

## Cách sử dụng

### Chạy chương trình

```bash
python main.py
```

### Menu chính

```text
██████╗ ██╗  ██╗ ██████╗ ██╗  ██╗ ██████╗  ██████╗ ██████╗ ██████╗ ██████╗ ███████╗
██╔══██╗██║  ██║██╔═══██╗██║  ██║██╔═══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
██████╔╝███████║██║   ██║███████║██║   ██║██║     ██║     ██║   ██║██║  ██║█████╗
██╔═══╝ ██╔══██║██║   ██║██╔══██║██║   ██║██║     ██║     ██║   ██║██║  ██║██╔══╝
██║     ██║  ██║╚██████╔╝██║  ██║╚██████╔╝╚██████╗╚██████╗╚██████╔╝██████╔╝███████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝

╔══════════════════════════════════════════════════════════════════════════════════╗
║                         IMAGE FORMAT CONVERTER                                   ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┌────────┬────────────────────────────────────────────────────────────────┐
│   1.   │ Chuyển đổi từ một URL                                          │
│   2.   │ Chuyển đổi từ file chứa danh sách URL                          │
│   3.   │ Chuyển đổi từ file JSON (movies format)                        │
│   4.   │ Lọc phim chưa tải từ JSON                                      │
│   5.   │ Xóa checkpoint (tiến trình đã lưu)                             │
│   6.   │ Hướng dẫn sử dụng                                              │
│   7.   │ Thoát                                                          │
└────────┴────────────────────────────────────────────────────────────────┘
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

Kết quả: Hiển thị dung lượng file gốc và sau chuyển đổi, % tiết kiệm
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
[>] Đang chuyển đổi: 100%|████████████| 4/4 [00:05<00:00, 0.75ảnh/s]

╔══════════════════════════════════════╗
║             KẾT QUẢ                  ║
╠══════════════════════════════════════╣
║ Thành công          │              4 ║
║ Thất bại            │              0 ║
║ Bỏ qua              │              0 ║
║ Tổng cộng           │              4 ║
╚══════════════════════════════════════╝
```

### 3. Chuyển đổi từ file JSON (Movies format)

Phù hợp cho việc chuyển đổi hàng loạt poster phim từ file JSON với hỗ trợ đa luồng.

**Format JSON yêu cầu:**

```json
[
  {
    "slug": "avatar-the-way-of-water",
    "url": "https://phimimg.com/upload/vod/avatar.jpg"
  },
  {
    "slug": "top-gun-maverick",
    "url": "https://phimimg.com/upload/vod/topgun.jpg"
  }
]
```

**Các bước:**

- Chọn option 3 trong menu
- **Tự động hiển thị danh sách file JSON** trong thư mục `mock` (nếu có):

  ```text
  Tìm thấy các file JSON trong thư mục mock:
     1. movies_posters.json (150.25 KB)
     2. movies_thumbs.json (98.50 KB)
     3. Nhập đường dẫn khác

  Chọn file (1-3):
  ```

- Chọn file từ danh sách hoặc nhập đường dẫn tùy chỉnh: `movies.json`
- Chọn định dạng đầu ra (khuyến nghị WEBP cho web)
- Nhập thư mục lưu file: `./posters`
- Tùy chọn số luồng xử lý (mặc định: 5, tối đa: 20)

**Kết quả:**

```text
[i] Sử dụng 5 luồng để xử lý
Đang chuyển đổi poster: 100%|████████| 2/2 [00:01<00:00, 1.33phim/s]

KẾT QUẢ:
   Thành công: 2
   Thất bại: 0
   Bỏ qua: 0
   Tổng cộng: 2
```

**Đặc điểm:**

- **Tự động phát hiện thư mục `mock`** - Hiển thị danh sách file JSON có sẵn với Rich table để chọn nhanh
- **Hiển thị thông tin file** - Tên file và kích thước (KB) trong bảng đẹp mắt
- File đầu ra tự động lấy tên từ trường `slug`: `avatar-the-way-of-water.webp`
- URL lấy từ trường `url`
- Tự động bỏ qua các bản ghi thiếu `slug` hoặc `url`
- Progress bar màu xanh lá với đơn vị "phim"
- Silent mode để không làm rối progress bar
- Kết quả hiển thị trong bảng đẹp với Rich

### 4. Lọc phim chưa tải từ JSON

Phù hợp cho việc kiểm tra tiến độ tải và tạo danh sách phim chưa tải.

**Các bước:**

- Chọn option 4 trong menu
- **Tự động hiển thị danh sách file JSON** trong thư mục `mock` (nếu có) hoặc nhập đường dẫn khác
- Nhập thư mục chứa ảnh đã tải (mặc định: `poster`)
- Nhập định dạng ảnh để kiểm tra (mặc định: `webp`)
- Nhập tên file output (mặc định: tự động tạo tên `_undownloaded.json`)

**Kết quả:**

```text
ℹ Đang phân tích 25298 phim từ file JSON...
ℹ Tìm thấy 24850 ảnh đã tải trong thư mục 'poster'

✓ Đã lưu 448 phim chưa tải vào: mock/movies_posters_undownloaded.json

╔══════════════════════════════════════╗
║          KẾT QUẢ LỌC                 ║
╠══════════════════════════════════════╣
║ Chưa tải           │            448  ║
║ Đã tải             │         24,850  ║
║ Tổng cộng          │         25,298  ║
║ Tiến độ            │          98.2%  ║
╚══════════════════════════════════════╝
```

**Đặc điểm:**

- **Tự động so sánh với thư mục ảnh** - Kiểm tra file đã tồn tại dựa vào slug
- **Không phân biệt định dạng** - Hỗ trợ jpg, jpeg, png, webp, gif, bmp
- **Tạo file JSON mới** - Chỉ chứa các phim chưa tải để xử lý tiếp
- **Hiển thị thống kê chi tiết** - Số phim chưa tải, đã tải, và phần trăm tiến độ
- **Tiết kiệm thời gian** - Không cần tải lại ảnh đã có

## Định dạng được hỗ trợ

| Định dạng | Mô tả                            | Ghi chú                            |
| --------- | -------------------------------- | ---------------------------------- |
| PNG       | Portable Network Graphics        | Hỗ trợ transparency                |
| JPEG/JPG  | Joint Photographic Experts Group | Không hỗ trợ transparency          |
| WEBP      | Web Picture format               | Định dạng hiện đại, kích thước nhỏ |
| BMP       | Bitmap                           | Định dạng cơ bản                   |
| GIF       | Graphics Interchange Format      | Hỗ trợ animation                   |
| TIFF      | Tagged Image File Format         | Chất lượng cao                     |
| ICO       | Icon format                      | Dùng cho icon                      |

## Ví dụ sử dụng

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

## Tính năng kỹ thuật

- **Xử lý đa luồng**:
  - Hỗ trợ 1-20 luồng đồng thời (mặc định: 5)
  - Thread-safe với Lock để đảm bảo checkpoint chính xác
  - Batch processing thông minh để tối ưu hiệu suất
  - Tăng tốc 3-5 lần so với xử lý tuần tự
- **Tự động xử lý transparency**: Khi chuyển sang JPEG, tự động thêm nền trắng cho ảnh có alpha channel
- **Tối ưu hóa nén**:
  - JPEG: Quality 85%, optimize=True
  - PNG: optimize=True
  - WEBP: Quality 80%, method=6 (nén tốt nhất), optimize=True
- **Checkpoint/Resume System**:
  - Tự động lưu tiến trình mỗi 10 ảnh/phim
  - File checkpoint: `.image_converter_checkpoint.json`
  - Phát hiện và hỏi resume khi chạy lại sau gián đoạn
  - Xử lý Ctrl+C thông minh - lưu trước khi thoát
  - Tự động xóa checkpoint khi hoàn thành
- **Progress bar với tqdm**: Hiển thị tiến độ, tốc độ (ảnh/s hoặc phim/s), ETA
- **Silent mode**: Tắt log chi tiết khi xử lý hàng loạt để progress bar đẹp hơn
- **Xử lý lỗi thông minh**: Bắt lỗi và thông báo chi tiết, tự động bỏ qua lỗi và tiếp tục
- **User-Agent**: Sử dụng User-Agent để tránh bị chặn khi tải ảnh
- **Timeout**: Giới hạn thời gian tải ảnh là 30 giây
- **So sánh dung lượng**: Hiển thị % tăng/giảm dung lượng sau chuyển đổi

## Xử lý lỗi

Chương trình sẽ thông báo chi tiết khi gặp lỗi:

- Lỗi kết nối hoặc URL không hợp lệ
- Lỗi khi xử lý ảnh (format không hỗ trợ)
- Lỗi khi tạo thư mục hoặc lưu file
- File URL không tồn tại hoặc không đọc được

## Cấu trúc thư mục

```text
image-format-converter/
├── main.py                          # File chính chứa toàn bộ logic
├── README.md                        # Hướng dẫn sử dụng chi tiết
├── requirements.txt                 # Danh sách thư viện cần thiết
├── urls-sample.txt                  # File mẫu chứa danh sách URL
├── movies-sample.json               # File JSON mẫu để test
├── mock/                            # Thư mục chứa file JSON (tùy chọn)
│   ├── movies_posters.json          # File JSON poster phim
│   └── movies_thumbs.json           # File JSON thumbnail phim
└── .image_converter_checkpoint.json # Checkpoint (tự động tạo khi cần)
```

## Checkpoint/Resume

### Cách hoạt động

Khi xử lý hàng loạt (option 2 hoặc 3), tool tự động:

1. **Lưu tiến trình mỗi 10 mục** vào file `.image_converter_checkpoint.json`
2. **Khi bị gián đoạn** (Ctrl+C, crash, mất mạng):

   ```text
   Đã bị gián đoạn! Đang lưu tiến trình...
   Đã lưu tiến trình: 1250/25298 phim
   Chạy lại và chọn 'Resume' để tiếp tục
   ```

3. **Khi chạy lại**, tự động phát hiện:

   ```text
   ℹ Phát hiện tiến trình chưa hoàn thành!

   ┌────────────────┬─────────────────┐
   │ File           │ movies.json     │
   │ Đã xử lý       │ 1250 phim       │
   └────────────────┴─────────────────┘

   Tiếp tục từ tiến trình cũ? (y/n):
   ```

4. **Khi hoàn thành** - Tự động xóa checkpoint

### Xóa checkpoint thủ công

Chọn **option 5** trong menu để xóa checkpoint:

```text
╭──────────── CHECKPOINT HIỆN TẠI ─────────────╮
│ Thông tin      │ Giá trị                     │
├────────────────┼─────────────────────────────┤
│ File           │ movies.json                 │
│ Đã xử lý       │ 1250 mục                    │
│ Định dạng      │ WEBP                        │
│ Thư mục        │ ./posters                   │
╰────────────────┴─────────────────────────────╯

Xác nhận xóa checkpoint? (y/n):
```

### Lợi ích

- **An toàn 100%** - Không lo mất công khi xử lý hàng nghìn ảnh
- **Linh hoạt** - Dừng bất cứ lúc nào, tiếp tục sau
- **Tự động** - Không cần làm gì, tool tự lo
- **Thông minh** - Chỉ hỏi resume khi cần thiết

## Ví dụ thực tế

### Chuyển đổi 25,000 poster phim sang WEBP

```text
ℹ Tìm thấy 25298 bộ phim trong file
ℹ Sử dụng 5 luồng để xử lý
[>] Đang chuyển đổi ảnh: 100%|████████| 25298/25298 [00:45:20<00:00, 9.30phim/s]

╔══════════════════════════════════════╗
║             KẾT QUẢ                  ║
╠══════════════════════════════════════╣
║ Thành công         │         24,850  ║
║ Thất bại           │            138  ║
║ Bỏ qua             │            310  ║
║ Tổng cộng          │         25,298  ║
╚══════════════════════════════════════╝

Thời gian: ~45 phút (5 luồng)
Dung lượng: Trung bình giảm 35% so với JPG gốc
```

## Tips & Best Practices

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

   - Xử lý hàng ngàn poster cùng lúc với đa luồng
   - Tên file tự động từ slug, dễ quản lý
   - Progress bar giúp theo dõi tiến độ
   - Tạo thư mục `mock/` để lưu các file JSON, tool sẽ tự động phát hiện và hiển thị
   - Điều chỉnh số luồng phù hợp với tốc độ mạng và cấu hình máy

5. **Sử dụng tính năng lọc** (option 4) để tối ưu:

   - Kiểm tra tiến độ tải sau khi bị gián đoạn
   - Tạo file JSON mới chỉ chứa phim chưa tải
   - Tiết kiệm thời gian không phải tải lại ảnh đã có
   - Theo dõi phần trăm hoàn thành của dự án

6. **Tips khác**:
   - Thêm **#** ở đầu dòng trong file URL để comment
   - Tạo thư mục riêng cho từng định dạng: `./webp`, `./jpeg`
   - Kiểm tra kết quả với vài ảnh trước khi xử lý hàng loạt
   - Đặt các file JSON vào thư mục `mock/` để chọn nhanh khi sử dụng option 3 hoặc 4
   - Sử dụng option 6 để xem hướng dẫn chi tiết ngay trong app

## Performance

- **Tốc độ đơn luồng**: ~1-2 ảnh/giây (tùy kích thước và kết nối)
- **Tốc độ đa luồng (5 luồng)**: ~5-10 ảnh/giây (tăng 3-5 lần)
- **Khuyến nghị số luồng**:
  - Mạng chậm: 3-5 luồng
  - Mạng nhanh: 5-10 luồng
  - Máy mạnh + mạng tốt: 10-20 luồng
- **WEBP method 6**: Chậm hơn nhưng nén tốt hơn 10-15%
- **Batch processing**: Xử lý song song với ThreadPoolExecutor
- **Memory efficient**: Xử lý từng ảnh một, không tốn RAM
- **Thread-safe**: Đảm bảo checkpoint chính xác trong môi trường đa luồng

## License

MIT License
