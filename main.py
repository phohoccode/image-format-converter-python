import os
import sys
import json
import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
from datetime import datetime
from urllib.parse import urlparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Global console instance
console = Console()

def print_success(message: str):
    """Print success message"""
    console.print(f"[bold green]✓[/bold green] {message}")

def print_error(message: str):
    """Print error message"""
    console.print(f"[bold red]✗[/bold red] {message}")

def print_info(message: str):
    """Print info message"""
    console.print(f"[bold cyan]ℹ[/bold cyan] {message}")

def print_warning(message: str):
    """Print warning message"""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")

def print_result_table(success: int, fail: int, skipped: int = None):
    """Print results in a beautiful table"""
    result_table = Table(title="KẾT QUẢ", box=box.DOUBLE_EDGE, border_style="bright_cyan", show_header=False)
    result_table.add_column("Status", style="bold", width=15)
    result_table.add_column("Count", justify="right", style="bold")
    
    result_table.add_row("[green]Thành công[/green]", f"[green]{success}[/green]")
    result_table.add_row("[red]Thất bại[/red]", f"[red]{fail}[/red]")
    if skipped is not None:
        result_table.add_row("[yellow]Bỏ qua[/yellow]", f"[yellow]{skipped}[/yellow]")
        result_table.add_row("[cyan]Tổng cộng[/cyan]", f"[cyan]{success + fail + skipped}[/cyan]")
    else:
        result_table.add_row("[cyan]Tổng cộng[/cyan]", f"[cyan]{success + fail}[/cyan]")
    
    console.print(result_table)


class ImageConverter:
    """Công cụ chuyển đổi định dạng ảnh từ URL"""
    
    SUPPORTED_FORMATS = ['PNG', 'JPEG', 'JPG', 'WEBP', 'BMP', 'GIF', 'TIFF', 'ICO']
    CHECKPOINT_FILE = '.image_converter_checkpoint.json'
    MAX_WORKERS = 5  # Số luồng tối đa mặc định
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.checkpoint_lock = Lock()  # Lock để đảm bảo thread-safe khi lưu checkpoint
    
    def validate_url(self, url: str) -> bool:
        """Kiểm tra URL có hợp lệ không"""
        try:
            result = urlparse(url.strip())
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False
    
    def save_checkpoint(self, file_path: str, processed_indices: list, output_format: str, output_dir: str):
        """Lưu tiến trình hiện tại vào checkpoint file (thread-safe)"""
        with self.checkpoint_lock:
            checkpoint_data = {
                'file_path': file_path,
                'processed_indices': processed_indices.copy(),  # Copy để tránh race condition
                'output_format': output_format,
                'output_dir': output_dir,
                'timestamp': datetime.now().isoformat()
            }
            try:
                with open(self.CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint_data, f, indent=2)
            except Exception as e:
                print(f"[!] Không thể lưu checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[dict]:
        """Đọc checkpoint nếu có"""
        if os.path.exists(self.CHECKPOINT_FILE):
            try:
                with open(self.CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def clear_checkpoint(self):
        """Xóa checkpoint file"""
        try:
            if os.path.exists(self.CHECKPOINT_FILE):
                os.remove(self.CHECKPOINT_FILE)
        except Exception:
            pass
    
    def download_image(self, url: str, silent: bool = False) -> tuple[Optional[Image.Image], int]:
        """Tải ảnh từ URL và trả về ảnh cùng với kích thước file gốc"""
        try:
            if not silent:
                print(f"[>] Đang tải ảnh từ: {url}")
            
            # Validate URL trước khi tải
            if not self.validate_url(url):
                if not silent:
                    print(f"[-] URL không hợp lệ: {url}")
                return None, 0
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            original_size = len(response.content)
            image = Image.open(BytesIO(response.content))
            if not silent:
                size_mb = original_size / (1024 * 1024)
                print(f"[+] Tải thành công! Kích thước: {image.size}, Định dạng: {image.format}, Dung lượng: {size_mb:.2f} MB ({original_size:,} bytes)")
            return image, original_size
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"[-] Lỗi khi tải ảnh: {e}")
            return None, 0
        except Exception as e:
            if not silent:
                print(f"[-] Lỗi khi xử lý ảnh: {e}")
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
            # Không in error để tránh rối progress bar
            return None
    
    def save_image(self, image: Image.Image, output_path: str, output_format: str, silent: bool = False, check_duplicate: bool = True) -> bool:
        """Lưu ảnh với định dạng mới"""
        try:
            output_format = output_format.upper()
            if output_format == 'JPG':
                output_format = 'JPEG'
            
            # Kiểm tra file đã tồn tại
            if check_duplicate and os.path.exists(output_path):
                if not silent:
                    print(f"[i] File đã tồn tại, bỏ qua: {output_path}")
                return False
            
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
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
                print(f"[+] Đã lưu: {output_path}")
                print(f"[i] Dung lượng file: {size_mb:.2f} MB ({saved_size:,} bytes)")
            return True
        except Exception as e:
            if not silent:
                print(f"[-] Lỗi khi lưu ảnh: {e}")
            return False
    
    def _worker_process_url(self, idx: int, url: str, output_format: str, output_dir: str, custom_name: Optional[str] = None) -> tuple[int, int]:
        """Worker function để xử lý URL trong thread pool
        Returns: (idx, status) where status: 1=success, 0=fail, -1=skip
        """
        # Tính tên file trước để kiểm tra
        if custom_name:
            filename = f"{custom_name}.{output_format.lower()}"
        else:
            url_path = url.split('?')[0]
            original_name = os.path.splitext(os.path.basename(url_path))[0]
            if not original_name:
                original_name = f"image_{hash(url) % 10000}"
            filename = f"{original_name}.{output_format.lower()}"
        
        output_path = os.path.join(output_dir, filename)
        
        # Kiểm tra file đã tồn tại
        if os.path.exists(output_path):
            return idx, -1  # Skip
        
        success = self.process_url(url, output_format, output_dir, custom_name, silent=True)
        return idx, 1 if success else 0
    
    def _worker_process_movie(self, idx: int, movie: dict, output_format: str, output_dir: str) -> tuple[int, int]:
        """Worker function để xử lý movie trong thread pool
        Returns: (idx, status) where status: 1=success, 0=fail, -1=skip
        """
        # Kiểm tra có trường poster và slug không
        if 'poster' not in movie or 'slug' not in movie:
            return idx, -1  # Skip
        
        poster_url = movie['poster']
        slug = movie['slug']
        
        # Bỏ qua nếu URL hoặc slug trống
        if not poster_url or not slug:
            return idx, -1  # Skip
        
        # Kiểm tra file đã tồn tại
        filename = f"{slug}.{output_format.lower()}"
        output_path = os.path.join(output_dir, filename)
        if os.path.exists(output_path):
            return idx, -1  # Skip
        
        # Xử lý chuyển đổi
        image, original_size = self.download_image(poster_url, silent=True)
        if image is not None:  # ✅ Check đúng cách
            converted_image = self.convert_image(image, output_format)
            if converted_image:
                filename = f"{slug}.{output_format.lower()}"
                output_path = os.path.join(output_dir, filename)
                
                if self.save_image(converted_image, output_path, output_format, silent=True):
                    return idx, 1  # Success
        
        return idx, 0  # Fail
    
    def process_url(self, url: str, output_format: str, output_dir: str, custom_name: Optional[str] = None, silent: bool = False) -> bool:
        """Xử lý một URL ảnh"""
        if not silent:
            print(f"\n{'='*60}")
        
        # Tải ảnh
        image, original_size = self.download_image(url, silent=silent)
        if image is None:
            return False
        
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
                print(f"[!] Dung lượng tăng: +{diff:,} bytes (+{percent:.1f}%)")
            else:
                print(f"[+] Dung lượng giảm: {abs(diff):,} bytes ({abs(percent):.1f}%)")
        
        return success
    
    def process_urls_from_file(self, file_path: str, output_format: str, output_dir: str, resume: bool = False, num_workers: int = None) -> tuple:
        """Xử lý nhiều URL từ file với hỗ trợ checkpoint và đa luồng"""
        if num_workers is None:
            num_workers = self.MAX_WORKERS
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not urls:
                print("[-] File không chứa URL nào!")
                return 0, 0
            
            # Kiểm tra resume checkpoint
            processed_indices = []
            start_index = 0
            if resume:
                checkpoint = self.load_checkpoint()
                if checkpoint and checkpoint.get('file_path') == file_path:
                    processed_indices = checkpoint.get('processed_indices', [])
                    start_index = len(processed_indices)
                    print(f"\n[>] Tiếp tục từ ảnh thứ {start_index + 1}/{len(urls)}")
            
            print(f"\n[i] Tìm thấy {len(urls)} URL trong file")
            print(f"[i] Sử dụng {num_workers} luồng để xử lý")
            if start_index > 0:
                print(f"[i] Đã xử lý: {start_index} ảnh")
            
            # Constants cho status
            STATUS_SUCCESS = 1
            STATUS_FAIL = 0
            STATUS_SKIP = -1
            
            # Đếm từ processed_results
            success_count = 0
            fail_count = 0
            skipped_count = 0
            
            for item in processed_indices:
                if isinstance(item, (list, tuple)):
                    _, status = item
                    if status == STATUS_SUCCESS:
                        success_count += 1
                    elif status == STATUS_FAIL:
                        fail_count += 1
                    else:
                        skipped_count += 1
                else:
                    # Format cũ để tương thích
                    if item >= 0:
                        success_count += 1
                    else:
                        fail_count += 1
            
            executor = None
            try:
                # Sử dụng ThreadPoolExecutor để xử lý đa luồng
                executor = ThreadPoolExecutor(max_workers=num_workers)
                with tqdm(total=len(urls), initial=start_index, desc="[>] Đang chuyển đổi", unit="ảnh", ncols=100, colour='cyan') as pbar:
                    # Submit tasks theo batch
                    batch_size = num_workers * 2
                    idx = start_index
                    
                    while idx < len(urls):
                        # Submit batch tasks
                        futures = {}
                        batch_end = min(idx + batch_size, len(urls))
                        
                        for i in range(idx, batch_end):
                            future = executor.submit(self._worker_process_url, i, urls[i], output_format, output_dir)
                            futures[future] = i
                        
                        # Xử lý kết quả khi hoàn thành
                        for future in as_completed(futures):
                            task_idx, status = future.result()
                            
                            # ✅ Thread-safe append
                            with self.checkpoint_lock:
                                processed_indices.append([task_idx, status])
                                if status == STATUS_SUCCESS:
                                    success_count += 1
                                elif status == STATUS_FAIL:
                                    fail_count += 1
                                else:  # STATUS_SKIP
                                    skipped_count += 1
                            
                            pbar.update(1)
                        
                        # Lưu checkpoint sau mỗi batch
                        self.save_checkpoint(file_path, processed_indices, output_format, output_dir)
                        idx = batch_end
                
                # Hoàn thành - xóa checkpoint
                self.clear_checkpoint()
                
            except KeyboardInterrupt:
                print("\n\n[!] Đã bị gián đoạn! Đang lưu tiến trình...")
                # ✅ Shutdown executor trước khi lưu
                if executor:
                    executor.shutdown(wait=True, cancel_futures=True)
                self.save_checkpoint(file_path, processed_indices, output_format, output_dir)
                print(f"[+] Đã lưu tiến trình: {len(processed_indices)}/{len(urls)} ảnh")
                print(f"[i] Chạy lại và chọn 'Resume' để tiếp tục")
                return success_count, fail_count, skipped_count
            finally:
                # ✅ Đảm bảo executor được đóng
                if executor:
                    executor.shutdown(wait=False)
            
            return success_count, fail_count, skipped_count
        except FileNotFoundError:
            print(f"[-] Không tìm thấy file: {file_path}")
            return 0, 0, 0
        except Exception as e:
            print(f"[-] Lỗi khi đọc file: {e}")
            return 0, 0, 0
    
    def process_movies_json(self, file_path: str, output_format: str, output_dir: str, resume: bool = False, num_workers: int = None) -> tuple:
        """Xử lý file JSON với định dạng movies (slug làm tên, poster làm URL) với đa luồng"""
        if num_workers is None:
            num_workers = self.MAX_WORKERS
        
        # Constants cho status
        STATUS_SUCCESS = 1
        STATUS_FAIL = 0
        STATUS_SKIP = -1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            if not movies:
                print("[-] File JSON không chứa dữ liệu!")
                return 0, 0, 0
            
            if not isinstance(movies, list):
                print("[-] File JSON phải là một mảng các object!")
                return 0, 0, 0
            
            # Kiểm tra resume checkpoint
            processed_results = []  # ✅ Lưu tuple (idx, status) thay vì magic number
            start_index = 0
            if resume:
                checkpoint = self.load_checkpoint()
                if checkpoint and checkpoint.get('file_path') == file_path:
                    # ✅ Chuyển đổi format cũ sang format mới
                    old_indices = checkpoint.get('processed_indices', [])
                    for idx_val in old_indices:
                        if isinstance(idx_val, list):  # Format mới
                            processed_results.append(tuple(idx_val))
                        else:  # Format cũ
                            if idx_val >= 0:
                                processed_results.append((idx_val, STATUS_SUCCESS))
                            elif idx_val == -999999:
                                processed_results.append((len(processed_results), STATUS_SKIP))
                            else:
                                processed_results.append((abs(idx_val), STATUS_FAIL))
                    start_index = len(processed_results)
                    print(f"\n[>] Tiếp tục từ phim thứ {start_index + 1}/{len(movies)}")
            
            print(f"\n[i] Tìm thấy {len(movies)} bộ phim trong file")
            print(f"[i] Sử dụng {num_workers} luồng để xử lý")
            if start_index > 0:
                print(f"[i] Đã xử lý: {start_index} phim")
            
            # Đếm từ processed_results
            success_count = sum(1 for _, status in processed_results if status == STATUS_SUCCESS)
            fail_count = sum(1 for _, status in processed_results if status == STATUS_FAIL)
            skipped_count = sum(1 for _, status in processed_results if status == STATUS_SKIP)
            
            executor = None
            try:
                # Sử dụng ThreadPoolExecutor để xử lý đa luồng
                executor = ThreadPoolExecutor(max_workers=num_workers)
                with tqdm(total=len(movies), initial=start_index, desc="[>] Đang chuyển đổi poster", unit="phim", ncols=100, colour='green') as pbar:
                    # Submit tasks theo batch
                    batch_size = num_workers * 2
                    idx = start_index
                    
                    while idx < len(movies):
                        # Submit batch tasks
                        futures = {}
                        batch_end = min(idx + batch_size, len(movies))
                        
                        for i in range(idx, batch_end):
                            future = executor.submit(self._worker_process_movie, i, movies[i], output_format, output_dir)
                            futures[future] = i
                        
                        # Xử lý kết quả khi hoàn thành
                        for future in as_completed(futures):
                            task_idx, status = future.result()
                            
                            # ✅ Thread-safe với lock bao toàn bộ operations
                            with self.checkpoint_lock:
                                processed_results.append((task_idx, status))
                                if status == STATUS_SUCCESS:
                                    success_count += 1
                                elif status == STATUS_FAIL:
                                    fail_count += 1
                                else:  # STATUS_SKIP
                                    skipped_count += 1
                            
                            pbar.update(1)
                        
                        # Lưu checkpoint sau mỗi batch - chuyển đổi sang list để JSON serializable
                        indices_for_checkpoint = [list(item) for item in processed_results]
                        self.save_checkpoint(file_path, indices_for_checkpoint, output_format, output_dir)
                        idx = batch_end
                
                # Hoàn thành - xóa checkpoint
                self.clear_checkpoint()
                
            except KeyboardInterrupt:
                print("\n\n[!] Đã bị gián đoạn! Đang lưu tiến trình...")
                # ✅ Shutdown executor trước khi lưu
                if executor:
                    executor.shutdown(wait=True, cancel_futures=True)
                indices_for_checkpoint = [list(item) for item in processed_results]
                self.save_checkpoint(file_path, indices_for_checkpoint, output_format, output_dir)
                print(f"[+] Đã lưu tiến trình: {len(processed_results)}/{len(movies)} phim")
                print(f"[i] Chạy lại và chọn 'Resume' để tiếp tục")
                return success_count, fail_count, skipped_count
            finally:
                # ✅ Đảm bảo executor được đóng
                if executor:
                    executor.shutdown(wait=False)
            
            return success_count, fail_count, skipped_count
        except FileNotFoundError:
            print(f"[-] Không tìm thấy file: {file_path}")
            return 0, 0, 0
        except json.JSONDecodeError as e:
            print(f"[-] Lỗi khi đọc file JSON: {e}")
            return 0, 0, 0
        except Exception as e:
            print(f"[-] Lỗi: {e}")
            return 0, 0, 0


def filter_undownloaded_movies(json_file: str, poster_dir: str, output_file: str, image_format: str = 'webp') -> tuple:
    """Lọc các phim chưa tải từ file JSON, so sánh với thư mục ảnh
    
    Args:
        json_file: Đường dẫn đến file JSON chứa danh sách phim
        poster_dir: Thư mục chứa ảnh poster đã tải
        output_file: File JSON output chứa danh sách phim chưa tải
        image_format: Định dạng ảnh để kiểm tra (mặc định: webp)
    
    Returns:
        tuple: (số phim chưa tải, số phim đã tải, tổng số phim)
    """
    try:
        # Đọc file JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            movies = json.load(f)
        
        if not movies or not isinstance(movies, list):
            print("[-] File JSON không hợp lệ!")
            return 0, 0, 0
        
        print(f"\n[i] Đang phân tích {len(movies)} phim từ file JSON...")
        
        # Lấy danh sách file ảnh đã tải (không phân biệt định dạng)
        downloaded_files = set()
        if os.path.exists(poster_dir):
            # Lấy tất cả các file ảnh với các định dạng phổ biến
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif', '*.bmp']:
                pattern = os.path.join(poster_dir, ext)
                for file_path in glob.glob(pattern):
                    # Lấy tên file không có extension
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    downloaded_files.add(filename.lower())
        
        print(f"[i] Tìm thấy {len(downloaded_files)} ảnh đã tải trong thư mục '{poster_dir}'")
        
        # Lọc các phim chưa tải
        undownloaded_movies = []
        downloaded_count = 0
        skipped_count = 0
        
        for movie in movies:
            # Kiểm tra có slug và poster không
            if 'slug' not in movie or 'poster' not in movie:
                skipped_count += 1
                continue
            
            slug = movie['slug']
            poster = movie['poster']
            
            if not slug or not poster:
                skipped_count += 1
                continue
            
            # Kiểm tra xem ảnh đã tải chưa
            if slug.lower() not in downloaded_files:
                undownloaded_movies.append(movie)
            else:
                downloaded_count += 1
        
        # Lưu danh sách phim chưa tải vào file mới
        if undownloaded_movies:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(undownloaded_movies, f, ensure_ascii=False, indent=2)
            print(f"\n[+] Đã lưu {len(undownloaded_movies)} phim chưa tải vào: {output_file}")
        else:
            print("\n[i] Tất cả phim đã được tải!")
        
        return len(undownloaded_movies), downloaded_count, len(movies)
        
    except FileNotFoundError:
        print(f"[-] Không tìm thấy file: {json_file}")
        return 0, 0, 0
    except json.JSONDecodeError as e:
        print(f"[-] Lỗi khi đọc file JSON: {e}")
        return 0, 0, 0
    except Exception as e:
        print(f"[-] Lỗi: {e}")
        return 0, 0, 0


def filter_movies_menu():
    """Menu lọc phim chưa tải"""
    console.print()
    # Kiểm tra thư mục mock và hiển thị các file JSON có sẵn
    mock_dir = "mock"
    json_files = []
    
    if os.path.exists(mock_dir) and os.path.isdir(mock_dir):
        json_files = [f for f in os.listdir(mock_dir) if f.endswith('.json')]
    
    if json_files:
        print_info("Tìm thấy các file JSON trong thư mục mock:")
        console.print()
        
        files_table = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
        files_table.add_column("#", style="bright_cyan", width=6)
        files_table.add_column("Filename", style="bright_white")
        files_table.add_column("Size", style="yellow", justify="right")
        
        for i, filename in enumerate(json_files, 1):
            file_path_display = os.path.join(mock_dir, filename)
            file_size = os.path.getsize(file_path_display)
            size_kb = file_size / 1024
            files_table.add_row(f"{i}.", filename, f"{size_kb:.2f} KB")
        
        files_table.add_row(f"{len(json_files) + 1}.", "Nhập đường dẫn khác", "")
        console.print(files_table)
        
        while True:
            try:
                choice = Prompt.ask(f"\n[bold]Chọn file (1-{len(json_files) + 1})[/bold]")
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(json_files):
                    json_file = os.path.join(mock_dir, json_files[choice_idx])
                    print_success(f"Đã chọn: [cyan]{json_file}[/cyan]")
                    break
                elif choice_idx == len(json_files):
                    json_file = Prompt.ask("\n[bold cyan]Nhập đường dẫn file JSON[/bold cyan]")
                    if not json_file or not os.path.exists(json_file):
                        print_error("Đường dẫn file không hợp lệ!")
                        return
                    break
                else:
                    print_error(f"Vui lòng chọn số từ 1 đến {len(json_files) + 1}")
            except ValueError:
                print_error("Vui lòng nhập số hợp lệ!")
    else:
        json_file = Prompt.ask("\n[bold cyan]Nhập đường dẫn file JSON[/bold cyan]")
        if not json_file or not os.path.exists(json_file):
            print_error("Đường dẫn file không hợp lệ!")
            return
    
    # Nhập thư mục chứa ảnh đã tải
    poster_dir = Prompt.ask("\n[bold cyan]Nhập đường dẫn thư mục chứa ảnh[/bold cyan] [dim](Enter = 'poster')[/dim]", default="poster")
    
    # Nhập định dạng ảnh để kiểm tra
    image_format = Prompt.ask("\n[bold cyan]Định dạng ảnh để kiểm tra[/bold cyan] [dim](Enter = 'webp')[/dim]", default="webp").lower()
    
    # Tạo tên file output
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    output_file = os.path.join(mock_dir, f"{base_name}_undownloaded.json")
    
    custom_output = Prompt.ask(f"\n[bold cyan]Tên file output[/bold cyan] [dim](Enter = '{output_file}')[/dim]", default=output_file)
    if custom_output and custom_output != output_file:
        output_file = custom_output
    
    console.print("\n[bold yellow]⏳ Đang phân tích...[/bold yellow]")
    undownloaded, downloaded, total = filter_undownloaded_movies(json_file, poster_dir, output_file, image_format)
    
    # Display filter results
    result_table = Table(title="KẾT QUẢ LỌC", box=box.DOUBLE_EDGE, border_style="bright_cyan", show_header=False)
    result_table.add_column("Status", style="bold", width=15)
    result_table.add_column("Count", justify="right", style="bold")
    
    result_table.add_row("[yellow]Chưa tải[/yellow]", f"[yellow]{undownloaded}[/yellow]")
    result_table.add_row("[green]Đã tải[/green]", f"[green]{downloaded}[/green]")
    result_table.add_row("[cyan]Tổng cộng[/cyan]", f"[cyan]{total}[/cyan]")
    if total > 0:
        percent = (downloaded / total) * 100
        result_table.add_row("[blue]Tiến độ[/blue]", f"[blue]{percent:.1f}%[/blue]")
    
    console.print()
    console.print(result_table)


def display_menu():
    """Hiển thị menu chính với Rich styling"""
    console = Console()
    
    # ASCII Art Logo với gradient màu
    logo = Text()
    logo_text = r"""
██████╗ ██╗  ██╗ ██████╗ ██╗  ██╗ ██████╗  ██████╗ ██████╗ ██████╗ ██████╗ ███████╗
██╔══██╗██║  ██║██╔═══██╗██║  ██║██╔═══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
██████╔╝███████║██║   ██║███████║██║   ██║██║     ██║     ██║   ██║██║  ██║█████╗  
██╔═══╝ ██╔══██║██║   ██║██╔══██║██║   ██║██║     ██║     ██║   ██║██║  ██║██╔══╝  
██║     ██║  ██║╚██████╔╝██║  ██║╚██████╔╝╚██████╗╚██████╗╚██████╔╝██████╔╝███████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
    """


    
    # Tạo gradient từ cyan sang magenta
    lines = logo_text.strip().split('\n')
    for i, line in enumerate(lines):
        # Tạo màu gradient từ cyan -> blue -> magenta
        color_progress = i / (len(lines) - 1)
        if color_progress < 0.5:
            color = f"rgb({int(0 + color_progress * 2 * 100)},{int(255 - color_progress * 2 * 100)},{255})"
        else:
            progress = (color_progress - 0.5) * 2
            color = f"rgb({int(100 + progress * 155)},{int(155 - progress * 155)},{255})"
        logo.append(line + "\n", style=color)
    
    console.print(logo)
    
    # Subtitle
    subtitle = Text("IMAGE FORMAT CONVERTER", style="bold bright_white")
    console.print(Panel(subtitle, box=box.DOUBLE, border_style="bright_cyan"))
    
    # Menu với table
    table = Table(show_header=False, box=box.ROUNDED, border_style="bright_blue", padding=(0, 2))
    table.add_column("Option", style="bright_cyan bold", width=8)
    table.add_column("Description", style="bright_white")
    
    table.add_row("1.", "Chuyển đổi từ một URL")
    table.add_row("2.", "Chuyển đổi từ file chứa danh sách URL")
    table.add_row("3.", "Chuyển đổi từ file JSON (movies format)")
    table.add_row("4.", "Lọc phim chưa tải từ JSON")
    table.add_row("5.", "Xóa checkpoint (tiến trình đã lưu)")
    table.add_row("6.", "Thoát", style="bright_red")
    
    console.print(table)
    console.print()


def get_output_format(converter: ImageConverter) -> str:
    """Cho người dùng chọn định dạng đầu ra"""
    console.print("\n[bold cyan]Chọn định dạng đầu ra:[/bold cyan]")
    
    format_table = Table(show_header=False, box=None, padding=(0, 2))
    format_table.add_column("Number", style="bright_cyan")
    format_table.add_column("Format", style="bright_white")
    
    for i, fmt in enumerate(converter.SUPPORTED_FORMATS, 1):
        format_table.add_row(f"{i}.", fmt)
    
    console.print(format_table)
    
    while True:
        try:
            choice = Prompt.ask(f"\n[bold]Nhập số (1-{len(converter.SUPPORTED_FORMATS)})[/bold]", default="4")
            index = int(choice) - 1
            if 0 <= index < len(converter.SUPPORTED_FORMATS):
                return converter.SUPPORTED_FORMATS[index]
            print_error(f"Vui lòng nhập số từ 1 đến {len(converter.SUPPORTED_FORMATS)}")
        except (ValueError, KeyboardInterrupt):
            print_error("Lựa chọn không hợp lệ!")
            raise


def get_output_directory() -> str:
    """Cho người dùng nhập đường dẫn lưu file"""
    console.print("\n[bold cyan]Nhập đường dẫn thư mục lưu ảnh:[/bold cyan]")
    console.print("[dim](Nhấn Enter để sử dụng thư mục hiện tại)[/dim]")
    
    while True:
        output_dir = Prompt.ask("[bold]Đường dẫn[/bold]", default=".")
        
        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(output_dir, exist_ok=True)
            abs_path = os.path.abspath(output_dir)
            print_success(f"Sẽ lưu vào: [cyan]{abs_path}[/cyan]")
            return output_dir
        except Exception as e:
            print_error(f"Không thể tạo thư mục: {e}")
            console.print("[yellow]Vui lòng nhập đường dẫn khác![/yellow]")


def process_single_url(converter: ImageConverter):
    """Xử lý chuyển đổi từ một URL"""
    console.print()
    url = Prompt.ask("[bold cyan]Nhập URL ảnh[/bold cyan]")
    if not url:
        print_error("URL không hợp lệ!")
        return
    
    # Validate URL format
    if not converter.validate_url(url):
        console.print()
        print_error(f"URL không hợp lệ: {url}")
        print_info("URL phải bắt đầu với http:// hoặc https://")
        return
    
    output_format = get_output_format(converter)
    output_dir = get_output_directory()
    
    custom_name = Prompt.ask("\n[bold cyan]Nhập tên file[/bold cyan] [dim](Enter để tự động)[/dim]", default="")
    custom_name = custom_name if custom_name else None
    
    console.print("\n[bold yellow]⏳ Bắt đầu chuyển đổi...[/bold yellow]")
    if converter.process_url(url, output_format, output_dir, custom_name):
        console.print()
        print_success("Chuyển đổi thành công!")
        console.print()
    else:
        console.print()
        print_error("Chuyển đổi thất bại!")
        console.print()


def process_file_urls(converter: ImageConverter):
    """Xử lý chuyển đổi từ file chứa danh sách URL"""
    console.print()
    # Kiểm tra checkpoint
    resume = False
    checkpoint = converter.load_checkpoint()
    if checkpoint:
        print_info("Phát hiện tiến trình chưa hoàn thành!")
        console.print()
        checkpoint_table = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
        checkpoint_table.add_column("Key", style="cyan")
        checkpoint_table.add_column("Value", style="white")
        checkpoint_table.add_row("File", checkpoint.get('file_path', 'N/A'))
        checkpoint_table.add_row("Đã xử lý", f"{len(checkpoint.get('processed_indices', []))} ảnh")
        console.print(checkpoint_table)
        
        if Confirm.ask("\n[bold cyan]Tiếp tục từ tiến trình cũ?[/bold cyan]"):
            resume = True
            file_path = checkpoint.get('file_path')
            output_format = checkpoint.get('output_format')
            output_dir = checkpoint.get('output_dir')
        else:
            converter.clear_checkpoint()
    
    if not resume:
        file_path = Prompt.ask("[bold cyan]Nhập đường dẫn file chứa URL[/bold cyan]")
        if not file_path:
            console.print()
            print_error("Đường dẫn file không hợp lệ!")
            return
        
        if not os.path.exists(file_path):
            console.print()
            print_error(f"File không tồn tại: {file_path}")
            return
        
        output_format = get_output_format(converter)
        output_dir = get_output_directory()
    
    # Cho phép chọn số luồng
    console.print(f"\n[bold cyan]Số luồng xử lý (mặc định: {converter.MAX_WORKERS}):[/bold cyan]")
    console.print("[dim](Nhấn Enter để sử dụng mặc định)[/dim]")
    num_workers_input = Prompt.ask("[bold]Số luồng[/bold]", default=str(converter.MAX_WORKERS))
    num_workers = converter.MAX_WORKERS
    if num_workers_input:
        try:
            num_workers = int(num_workers_input)
            if num_workers < 1:
                print_warning("Số luồng phải >= 1, sử dụng mặc định")
                num_workers = converter.MAX_WORKERS
            elif num_workers > 20:
                print_warning("Số luồng quá lớn (max 20), sử dụng 20")
                num_workers = 20
        except ValueError:
            print_warning("Giá trị không hợp lệ, sử dụng mặc định")
    
    console.print("\n[bold yellow]⏳ Bắt đầu chuyển đổi...[/bold yellow]")
    success, fail, skipped = converter.process_urls_from_file(file_path, output_format, output_dir, resume=resume, num_workers=num_workers)
    
    console.print()
    print_result_table(success, fail, skipped)


def clear_checkpoint_menu(converter: ImageConverter):
    """Xóa checkpoint đã lưu"""
    console.print()
    checkpoint = converter.load_checkpoint()
    if not checkpoint:
        print_info("Không có checkpoint nào được lưu.")
        console.print()
        return
    
    # Display checkpoint info
    checkpoint_info = Table(title="CHECKPOINT HIỆN TẠI", box=box.ROUNDED, border_style="yellow")
    checkpoint_info.add_column("Thông tin", style="cyan")
    checkpoint_info.add_column("Giá trị", style="white")
    
    checkpoint_info.add_row("File", checkpoint.get('file_path', 'N/A'))
    checkpoint_info.add_row("Đã xử lý", f"{len(checkpoint.get('processed_indices', []))} mục")
    checkpoint_info.add_row("Định dạng", checkpoint.get('output_format', 'N/A'))
    checkpoint_info.add_row("Thư mục", checkpoint.get('output_dir', 'N/A'))
    
    console.print()
    console.print(checkpoint_info)
    
    if Confirm.ask("\n[bold yellow]Xác nhận xóa checkpoint?[/bold yellow]"):
        converter.clear_checkpoint()
        console.print()
        print_success("Đã xóa checkpoint thành công!")
        console.print()
    else:
        console.print()
        print_warning("Đã hủy xóa checkpoint.")
        console.print()


def process_movies_json(converter: ImageConverter):
    """Xử lý chuyển đổi từ file JSON movies"""
    console.print()
    # Kiểm tra checkpoint
    resume = False
    checkpoint = converter.load_checkpoint()
    if checkpoint:
        print_info("Phát hiện tiến trình chưa hoàn thành!")
        console.print()
        checkpoint_table = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
        checkpoint_table.add_column("Key", style="cyan")
        checkpoint_table.add_column("Value", style="white")
        checkpoint_table.add_row("File", checkpoint.get('file_path', 'N/A'))
        checkpoint_table.add_row("Đã xử lý", f"{len(checkpoint.get('processed_indices', []))} phim")
        console.print(checkpoint_table)
        
        if Confirm.ask("\n[bold cyan]Tiếp tục từ tiến trình cũ?[/bold cyan]"):
            resume = True
            file_path = checkpoint.get('file_path')
            output_format = checkpoint.get('output_format')
            output_dir = checkpoint.get('output_dir')
        else:
            converter.clear_checkpoint()
    
    if not resume:
        # Kiểm tra thư mục mock và hiển thị các file JSON có sẵn
        mock_dir = "mock"
        json_files = []
        
        if os.path.exists(mock_dir) and os.path.isdir(mock_dir):
            json_files = [f for f in os.listdir(mock_dir) if f.endswith('.json')]
            
            if json_files:
                print_info("Tìm thấy các file JSON trong thư mục mock:")
                console.print()
                
                files_table = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
                files_table.add_column("#", style="bright_cyan", width=6)
                files_table.add_column("Filename", style="bright_white")
                files_table.add_column("Size", style="yellow", justify="right")
                
                for i, filename in enumerate(json_files, 1):
                    file_path_display = os.path.join(mock_dir, filename)
                    file_size = os.path.getsize(file_path_display)
                    size_kb = file_size / 1024
                    files_table.add_row(f"{i}.", filename, f"{size_kb:.2f} KB")
                
                files_table.add_row(f"{len(json_files) + 1}.", "Nhập đường dẫn khác", "")
                console.print(files_table)
                
                while True:
                    try:
                        choice = Prompt.ask(f"\n[bold]Chọn file (1-{len(json_files) + 1})[/bold]")
                        choice_idx = int(choice) - 1
                        
                        if 0 <= choice_idx < len(json_files):
                            file_path = os.path.join(mock_dir, json_files[choice_idx])
                            print_success(f"Đã chọn: [cyan]{file_path}[/cyan]")
                            break
                        elif choice_idx == len(json_files):
                            # Người dùng chọn nhập đường dẫn khác
                            file_path = Prompt.ask("\n[bold cyan]Nhập đường dẫn file JSON[/bold cyan]")
                            if not file_path:
                                print_error("Đường dẫn file không hợp lệ!")
                                return
                            
                            if not os.path.exists(file_path):
                                print_error(f"File không tồn tại: {file_path}")
                                return
                            break
                        else:
                            print_error(f"Vui lòng chọn số từ 1 đến {len(json_files) + 1}")
                    except ValueError:
                        print_error("Vui lòng nhập số hợp lệ!")
            else:
                # Thư mục mock tồn tại nhưng không có file JSON
                file_path = Prompt.ask("\n[bold cyan]Nhập đường dẫn file JSON[/bold cyan]")
                if not file_path:
                    print_error("Đường dẫn file không hợp lệ!")
                    return
                
                if not os.path.exists(file_path):
                    print_error(f"File không tồn tại: {file_path}")
                    return
        else:
            # Thư mục mock không tồn tại
            file_path = Prompt.ask("\n[bold cyan]Nhập đường dẫn file JSON[/bold cyan]")
            if not file_path:
                print_error("Đường dẫn file không hợp lệ!")
                return
            
            if not os.path.exists(file_path):
                print_error(f"File không tồn tại: {file_path}")
                return
        
        output_format = get_output_format(converter)
        output_dir = get_output_directory()
    
    # Cho phép chọn số luồng
    console.print(f"\n[bold cyan]Số luồng xử lý (mặc định: {converter.MAX_WORKERS}):[/bold cyan]")
    console.print("[dim](Nhấn Enter để sử dụng mặc định)[/dim]")
    num_workers_input = Prompt.ask("[bold]Số luồng[/bold]", default=str(converter.MAX_WORKERS))
    num_workers = converter.MAX_WORKERS
    if num_workers_input:
        try:
            num_workers = int(num_workers_input)
            if num_workers < 1:
                print_warning("Số luồng phải >= 1, sử dụng mặc định")
                num_workers = converter.MAX_WORKERS
            elif num_workers > 20:
                print_warning("Số luồng quá lớn (max 20), sử dụng 20")
                num_workers = 20
        except ValueError:
            print_warning("Giá trị không hợp lệ, sử dụng mặc định")
    
    console.print("\n[bold yellow]⏳ Bắt đầu chuyển đổi...[/bold yellow]")
    success, fail, skipped = converter.process_movies_json(file_path, output_format, output_dir, resume=resume, num_workers=num_workers)
    
    console.print()
    print_result_table(success, fail, skipped)


def main():
    """Hàm chính"""
    converter = ImageConverter()
    
    while True:
        try:
            display_menu()
            choice = Prompt.ask("[bold]Chọn chức năng (1-6)[/bold]", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == '1':
                process_single_url(converter)
            elif choice == '2':
                process_file_urls(converter)
            elif choice == '3':
                process_movies_json(converter)
            elif choice == '4':
                filter_movies_menu()
            elif choice == '5':
                clear_checkpoint_menu(converter)
            elif choice == '6':
                console.print("\n[bold cyan]👋 Tạm biệt![/bold cyan]")
                sys.exit(0)
        
        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]👋 Tạm biệt![/bold cyan]")
            sys.exit(0)
        except Exception as e:
            print_error(f"Đã xảy ra lỗi: {e}")


if __name__ == "__main__":
    main()