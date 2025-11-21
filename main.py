import os
import sys
import json
import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm


class ImageConverter:
    """Công cụ chuyển đổi định dạng ảnh từ URL"""
    
    SUPPORTED_FORMATS = ['PNG', 'JPEG', 'JPG', 'WEBP', 'BMP', 'GIF', 'TIFF', 'ICO']
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_image(self, url: str, silent: bool = False) -> Optional[tuple[Image.Image, int]]:
        """Tải ảnh từ URL và trả về ảnh cùng với kích thước file gốc"""
        try:
            if not silent:
                print(f"📥 Đang tải ảnh từ: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            original_size = len(response.content)
            image = Image.open(BytesIO(response.content))
            if not silent:
                size_mb = original_size / (1024 * 1024)
                print(f"✅ Tải thành công! Kích thước: {image.size}, Định dạng: {image.format}, Dung lượng: {size_mb:.2f} MB ({original_size:,} bytes)")
            return image, original_size
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi tải ảnh: {e}")
            return None, 0
        except Exception as e:
            print(f"❌ Lỗi khi xử lý ảnh: {e}")
            return None, 0
    
    def convert_image(self, image: Image.Image, output_format: str) -> Optional[Image.Image]:
        """Chuyển đổi định dạng ảnh"""
        try:
            output_format = output_format.upper()
            
            # Xử lý chuyển đổi cho các định dạng đặc biệt
            if output_format in ['JPEG', 'JPG']:
                # JPEG không hỗ trợ transparency, chuyển sang RGB
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
            elif output_format == 'PNG':
                # Đảm bảo PNG có alpha channel nếu cần
                if image.mode not in ('RGBA', 'RGB'):
                    image = image.convert('RGBA')
            elif output_format in ['BMP', 'ICO']:
                # BMP và ICO thường sử dụng RGB
                if image.mode not in ('RGB', 'RGBA'):
                    image = image.convert('RGB')
            
            return image
        except Exception as e:
            print(f"❌ Lỗi khi chuyển đổi ảnh: {e}")
            return None
    
    def save_image(self, image: Image.Image, output_path: str, output_format: str, silent: bool = False) -> bool:
        """Lưu ảnh với định dạng mới"""
        try:
            output_format = output_format.upper()
            if output_format == 'JPG':
                output_format = 'JPEG'
            
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Lưu ảnh với các tham số tối ưu
            save_kwargs = {'format': output_format}
            if output_format == 'JPEG':
                save_kwargs['quality'] = 85
                save_kwargs['optimize'] = True
            elif output_format == 'PNG':
                save_kwargs['optimize'] = True
            elif output_format == 'WEBP':
                save_kwargs['quality'] = 80  # Giảm quality để giảm dung lượng
                save_kwargs['method'] = 6    # Nén mạnh hơn (0-6, 6 là chậm nhưng nén tốt nhất)
                save_kwargs['optimize'] = True
            
            image.save(output_path, **save_kwargs)
            
            if not silent:
                # Hiển thị thông tin dung lượng file sau khi lưu
                saved_size = os.path.getsize(output_path)
                size_mb = saved_size / (1024 * 1024)
                print(f"💾 Đã lưu: {output_path}")
                print(f"📦 Dung lượng file: {size_mb:.2f} MB ({saved_size:,} bytes)")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi lưu ảnh: {e}")
            return False
    
    def process_url(self, url: str, output_format: str, output_dir: str, custom_name: Optional[str] = None, silent: bool = False) -> bool:
        """Xử lý một URL ảnh"""
        if not silent:
            print(f"\n{'='*60}")
        
        # Tải ảnh
        result = self.download_image(url, silent=silent)
        if not result[0]:
            return False
        
        image, original_size = result
        
        # Chuyển đổi định dạng
        converted_image = self.convert_image(image, output_format)
        if not converted_image:
            return False
        
        # Tạo tên file
        if custom_name:
            filename = f"{custom_name}.{output_format.lower()}"
        else:
            # Lấy tên file từ URL
            url_path = url.split('?')[0]  # Bỏ query parameters
            original_name = os.path.splitext(os.path.basename(url_path))[0]
            if not original_name:
                original_name = f"image_{hash(url) % 10000}"
            filename = f"{original_name}.{output_format.lower()}"
        
        output_path = os.path.join(output_dir, filename)
        
        # Lưu ảnh
        success = self.save_image(converted_image, output_path, output_format, silent=silent)
        
        if success and original_size > 0 and not silent:
            saved_size = os.path.getsize(output_path)
            diff = saved_size - original_size
            percent = (diff / original_size) * 100
            
            if diff > 0:
                print(f"⚠️  Dung lượng tăng: +{diff:,} bytes (+{percent:.1f}%)")
            else:
                print(f"✅ Dung lượng giảm: {abs(diff):,} bytes ({abs(percent):.1f}%)")
        
        return success
    
    def process_urls_from_file(self, file_path: str, output_format: str, output_dir: str) -> tuple:
        """Xử lý nhiều URL từ file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not urls:
                print("❌ File không chứa URL nào!")
                return 0, 0
            
            print(f"\n📋 Tìm thấy {len(urls)} URL trong file")
            success_count = 0
            fail_count = 0
            
            # Sử dụng tqdm để hiển thị progress bar
            with tqdm(total=len(urls), desc="🔄 Đang chuyển đổi", unit="ảnh", ncols=100, colour='cyan') as pbar:
                for url in urls:
                    if self.process_url(url, output_format, output_dir, silent=True):
                        success_count += 1
                    else:
                        fail_count += 1
                    pbar.update(1)
            
            return success_count, fail_count
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file: {file_path}")
            return 0, 0
        except Exception as e:
            print(f"❌ Lỗi khi đọc file: {e}")
            return 0, 0
    
    def process_movies_json(self, file_path: str, output_format: str, output_dir: str) -> tuple:
        """Xử lý file JSON với định dạng movies (slug làm tên, poster làm URL)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            if not movies:
                print("❌ File JSON không chứa dữ liệu!")
                return 0, 0
            
            if not isinstance(movies, list):
                print("❌ File JSON phải là một mảng các object!")
                return 0, 0
            
            print(f"\n📋 Tìm thấy {len(movies)} bộ phim trong file")
            success_count = 0
            fail_count = 0
            skipped_count = 0
            
            # Sử dụng tqdm để hiển thị progress bar
            with tqdm(total=len(movies), desc="🎬 Đang chuyển đổi poster", unit="phim", ncols=100, colour='green') as pbar:
                for movie in movies:
                    # Kiểm tra có trường poster và slug không
                    if 'poster' not in movie or 'slug' not in movie:
                        skipped_count += 1
                        pbar.update(1)
                        continue
                    
                    poster_url = movie['poster']
                    slug = movie['slug']
                    
                    # Bỏ qua nếu URL hoặc slug trống
                    if not poster_url or not slug:
                        skipped_count += 1
                        pbar.update(1)
                        continue
                    
                    # Xử lý chuyển đổi (không in log chi tiết để không làm rối progress bar)
                    result = self.download_image(poster_url, silent=True)
                    if result[0]:
                        image, original_size = result
                        converted_image = self.convert_image(image, output_format)
                        if converted_image:
                            filename = f"{slug}.{output_format.lower()}"
                            output_path = os.path.join(output_dir, filename)
                            
                            if self.save_image(converted_image, output_path, output_format, silent=True):
                                success_count += 1
                            else:
                                fail_count += 1
                        else:
                            fail_count += 1
                    else:
                        fail_count += 1
                    
                    pbar.update(1)
            
            return success_count, fail_count, skipped_count
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file: {file_path}")
            return 0, 0, 0
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi khi đọc file JSON: {e}")
            return 0, 0, 0
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return 0, 0, 0


def display_menu():
    """Hiển thị menu chính"""
    print("\n" + "="*60)
    print("🖼️  IMAGE FORMAT CONVERTER")
    print("="*60)
    print("1. Chuyển đổi từ một URL")
    print("2. Chuyển đổi từ file chứa danh sách URL")
    print("3. Chuyển đổi từ file JSON (movies format)")
    print("4. Thoát")
    print("="*60)


def get_output_format(converter: ImageConverter) -> str:
    """Cho người dùng chọn định dạng đầu ra"""
    print("\n📝 Chọn định dạng đầu ra:")
    for i, fmt in enumerate(converter.SUPPORTED_FORMATS, 1):
        print(f"{i}. {fmt}")
    
    while True:
        try:
            choice = input(f"\nNhập số (1-{len(converter.SUPPORTED_FORMATS)}): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(converter.SUPPORTED_FORMATS):
                return converter.SUPPORTED_FORMATS[index]
            print(f"❌ Vui lòng nhập số từ 1 đến {len(converter.SUPPORTED_FORMATS)}")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Lựa chọn không hợp lệ!")


def get_output_directory() -> str:
    """Cho người dùng nhập đường dẫn lưu file"""
    print("\n📁 Nhập đường dẫn thư mục lưu ảnh:")
    print("   (Nhấn Enter để sử dụng thư mục hiện tại)")
    
    while True:
        output_dir = input("Đường dẫn: ").strip()
        if not output_dir:
            output_dir = "."
        
        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(output_dir, exist_ok=True)
            abs_path = os.path.abspath(output_dir)
            print(f"✅ Sẽ lưu vào: {abs_path}")
            return output_dir
        except Exception as e:
            print(f"❌ Không thể tạo thư mục: {e}")
            print("Vui lòng nhập đường dẫn khác!")


def process_single_url(converter: ImageConverter):
    """Xử lý chuyển đổi từ một URL"""
    url = input("\n🔗 Nhập URL ảnh: ").strip()
    if not url:
        print("❌ URL không hợp lệ!")
        return
    
    output_format = get_output_format(converter)
    output_dir = get_output_directory()
    
    custom_name = input("\n📝 Nhập tên file (nhấn Enter để tự động): ").strip()
    custom_name = custom_name if custom_name else None
    
    print("\n🚀 Bắt đầu chuyển đổi...")
    if converter.process_url(url, output_format, output_dir, custom_name):
        print("\n✅ Chuyển đổi thành công!")
    else:
        print("\n❌ Chuyển đổi thất bại!")


def process_file_urls(converter: ImageConverter):
    """Xử lý chuyển đổi từ file chứa danh sách URL"""
    file_path = input("\n📄 Nhập đường dẫn file chứa URL: ").strip()
    if not file_path:
        print("❌ Đường dẫn file không hợp lệ!")
        return
    
    if not os.path.exists(file_path):
        print(f"❌ File không tồn tại: {file_path}")
        return
    
    output_format = get_output_format(converter)
    output_dir = get_output_directory()
    
    print("\n🚀 Bắt đầu chuyển đổi...")
    success, fail = converter.process_urls_from_file(file_path, output_format, output_dir)
    
    print(f"\n{'='*60}")
    print(f"📊 KẾT QUẢ:")
    print(f"   ✅ Thành công: {success}")
    print(f"   ❌ Thất bại: {fail}")
    print(f"   📊 Tổng cộng: {success + fail}")
    print(f"{'='*60}")


def process_movies_json(converter: ImageConverter):
    """Xử lý chuyển đổi từ file JSON movies"""
    file_path = input("\n📄 Nhập đường dẫn file JSON: ").strip()
    if not file_path:
        print("❌ Đường dẫn file không hợp lệ!")
        return
    
    if not os.path.exists(file_path):
        print(f"❌ File không tồn tại: {file_path}")
        return
    
    output_format = get_output_format(converter)
    output_dir = get_output_directory()
    
    print("\n🚀 Bắt đầu chuyển đổi...")
    success, fail, skipped = converter.process_movies_json(file_path, output_format, output_dir)
    
    print(f"\n{'='*60}")
    print(f"📊 KẾT QUẢ:")
    print(f"   ✅ Thành công: {success}")
    print(f"   ❌ Thất bại: {fail}")
    print(f"   ⏭️  Bỏ qua: {skipped}")
    print(f"   📊 Tổng cộng: {success + fail + skipped}")
    print(f"{'='*60}")


def main():
    """Hàm chính"""
    converter = ImageConverter()
    
    while True:
        try:
            display_menu()
            choice = input("Chọn chức năng (1-4): ").strip()
            
            if choice == '1':
                process_single_url(converter)
            elif choice == '2':
                process_file_urls(converter)
            elif choice == '3':
                process_movies_json(converter)
            elif choice == '4':
                print("\n👋 Tạm biệt!")
                sys.exit(0)
            else:
                print("❌ Lựa chọn không hợp lệ!")
        
        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Đã xảy ra lỗi: {e}")


if __name__ == "__main__":
    main()
