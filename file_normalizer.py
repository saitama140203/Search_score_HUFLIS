import os
from pathlib import Path
import shutil
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_normalizer.log'),
        logging.StreamHandler()
    ]
)

class FileNameNormalizer:
    def __init__(self, base_path="data_diem_dhnn"):
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        
        # Mapping để chuẩn hóa tên file
        self.name_mapping = {
            # Tiếng Anh
            "anh bien dịch": "anhbiendich",
            "anh du lịch": "anhdulich", 
            "anh ngữ văn": "anhnguvan",
            "anh phiên dịch": "anhphiendich",
            "anh sp tiểu học": "anhsptieuhoc",
            
            # Tiếng Trung
            "trung biên dịch": "trungbiendich",
            "trung phiên dịch": "trungphiendich", 
            "trung thương mại": "trungthuongmai",
            
            # Viết hoa thành viết thường
            "Hàn": "hàn",
            
            # Các tên khác giữ nguyên
            "anh": "anh",
            "nga": "nga",
            "nhật": "nhật",
            "pháp": "pháp", 
            "phap": "pháp",  # Chuẩn hóa pháp/phap
            "qth": "qth",
            "spanh": "spanh",
            "spphap": "spphap",
            "sptrung": "sptrung",
            "trung": "trung",
            "vnh": "vnh"
        }
        
        self.renamed_files = []
        self.skipped_files = []
    
    def normalize_filename(self, filename):
        """Chuẩn hóa tên file"""
        # Loại bỏ extension
        name_without_ext = filename.stem
        
        # Tìm trong mapping
        if name_without_ext in self.name_mapping:
            return self.name_mapping[name_without_ext]
        
        # Nếu không có trong mapping, chuẩn hóa cơ bản
        normalized = name_without_ext.lower()
        normalized = normalized.replace(" ", "")
        normalized = normalized.replace("_", "")
        normalized = normalized.replace("-", "")
        
        return normalized
    
    def analyze_current_structure(self):
        """Phân tích cấu trúc hiện tại"""
        print("Phân tích cấu trúc file hiện tại:")
        print("="*50)
        
        all_files = {}
        
        for semester_dir in self.raw_path.iterdir():
            if not semester_dir.is_dir():
                continue
                
            semester = semester_dir.name
            all_files[semester] = {}
            
            for khoa_dir in semester_dir.iterdir():
                if not khoa_dir.is_dir():
                    continue
                    
                khoa = khoa_dir.name
                files = [f.stem for f in khoa_dir.glob("*.xls")]
                all_files[semester][khoa] = files
                
                print(f"\n{semester}/{khoa}:")
                for file in sorted(files):
                    print(f"  - {file}")
        
        return all_files
    
    def create_standardized_mapping(self):
        """Tạo mapping chuẩn cho tất cả file"""
        all_files = self.analyze_current_structure()
        
        # Thu thập tất cả tên file unique
        unique_names = set()
        for semester in all_files:
            for khoa in all_files[semester]:
                unique_names.update(all_files[semester][khoa])
        
        print(f"\nTất cả tên file unique ({len(unique_names)}):")
        for name in sorted(unique_names):
            normalized = self.normalize_filename(Path(name))
            print(f"  {name} -> {normalized}")
        
        return unique_names
    
    def preview_changes(self):
        """Xem trước các thay đổi sẽ được thực hiện"""
        print("\nXem trước các thay đổi sẽ thực hiện:")
        print("="*50)
        
        changes = []
        
        for semester_dir in self.raw_path.iterdir():
            if not semester_dir.is_dir():
                continue
                
            semester = semester_dir.name
            
            for khoa_dir in semester_dir.iterdir():
                if not khoa_dir.is_dir():
                    continue
                    
                khoa = khoa_dir.name
                
                for file_path in khoa_dir.glob("*.xls"):
                    old_name = file_path.stem
                    new_name = self.normalize_filename(file_path)
                    
                    if old_name != new_name:
                        changes.append({
                            'path': str(file_path),
                            'old_name': old_name,
                            'new_name': new_name,
                            'semester': semester,
                            'khoa': khoa
                        })
        
        if not changes:
            print("Không có file nào cần đổi tên.")
            return changes
        
        print(f"Sẽ đổi tên {len(changes)} file:")
        for change in changes:
            print(f"  {change['semester']}/{change['khoa']}: {change['old_name']} -> {change['new_name']}")
        
        return changes
    
    def apply_changes(self, dry_run=True):
        """Áp dụng các thay đổi"""
        changes = self.preview_changes()
        
        if not changes:
            return
        
        if dry_run:
            print(f"\nDRY RUN - Sẽ thực hiện {len(changes)} thay đổi")
            return
        
        print(f"\nBắt đầu đổi tên {len(changes)} file...")
        
        for change in changes:
            old_path = Path(change['path'])
            new_path = old_path.parent / f"{change['new_name']}.xls"
            
            try:
                old_path.rename(new_path)
                self.renamed_files.append({
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                    'old_name': change['old_name'],
                    'new_name': change['new_name']
                })
                logging.info(f"Đổi tên: {change['old_name']} -> {change['new_name']}")
                
            except Exception as e:
                self.skipped_files.append({
                    'path': str(old_path),
                    'error': str(e)
                })
                logging.error(f"Lỗi đổi tên {old_path}: {str(e)}")
        
        print(f"Hoàn thành! Đã đổi tên {len(self.renamed_files)} file.")
        if self.skipped_files:
            print(f"Bỏ qua {len(self.skipped_files)} file do lỗi.")
    
    def create_backup(self):
        """Tạo backup trước khi thay đổi"""
        backup_path = self.base_path / "backup_raw"
        
        if backup_path.exists():
            print(f"Backup đã tồn tại: {backup_path}")
            return backup_path
        
        print(f"Tạo backup: {backup_path}")
        shutil.copytree(self.raw_path, backup_path)
        return backup_path
    
    def verify_consistency(self):
        """Kiểm tra tính nhất quán sau khi chuẩn hóa"""
        print("\nKiểm tra tính nhất quán:")
        print("="*30)
        
        all_files = {}
        
        for semester_dir in self.raw_path.iterdir():
            if not semester_dir.is_dir():
                continue
                
            semester = semester_dir.name
            all_files[semester] = {}
            
            for khoa_dir in semester_dir.iterdir():
                if not khoa_dir.is_dir():
                    continue
                    
                khoa = khoa_dir.name
                files = set(f.stem for f in khoa_dir.glob("*.xls"))
                all_files[semester][khoa] = files
        
        # So sánh các khóa trong cùng học kỳ
        for semester in all_files:
            khoa_list = list(all_files[semester].keys())
            if len(khoa_list) < 2:
                continue
            
            print(f"\n{semester}:")
            
            # Tìm file có trong khóa này nhưng không có trong khóa khác
            all_files_in_semester = set()
            for khoa in khoa_list:
                all_files_in_semester.update(all_files[semester][khoa])
            
            for khoa in khoa_list:
                missing = all_files_in_semester - all_files[semester][khoa]
                if missing:
                    print(f"  {khoa} thiếu: {sorted(missing)}")
                else:
                    print(f"  {khoa}: Đầy đủ ({len(all_files[semester][khoa])} file)")
    
    def print_summary(self):
        """In tóm tắt"""
        print("\n" + "="*50)
        print("TÓM TẮT CHUẨN HÓA TÊN FILE")
        print("="*50)
        print(f"File đã đổi tên: {len(self.renamed_files)}")
        print(f"File bỏ qua: {len(self.skipped_files)}")
        
        if self.renamed_files:
            print(f"\nCác file đã đổi tên:")
            for item in self.renamed_files:
                print(f"  {item['old_name']} -> {item['new_name']}")
        
        if self.skipped_files:
            print(f"\nCác file bỏ qua:")
            for item in self.skipped_files:
                print(f"  {item['path']}: {item['error']}")

def main():
    print("FILE NAME NORMALIZER - Chuẩn hóa tên file")
    print("="*50)
    
    normalizer = FileNameNormalizer()
    
    if not normalizer.raw_path.exists():
        print(f"Không tìm thấy thư mục raw: {normalizer.raw_path}")
        return
    
    # Bước 1: Phân tích cấu trúc hiện tại
    normalizer.create_standardized_mapping()
    
    # Bước 2: Xem trước thay đổi
    print("\n" + "="*50)
    changes = normalizer.preview_changes()
    
    if not changes:
        print("Tất cả file đã có tên chuẩn.")
        normalizer.verify_consistency()
        return
    
    # Bước 3: Xác nhận từ user
    print("\n" + "="*50)
    response = input("Bạn có muốn thực hiện các thay đổi này? (y/n): ").lower()
    
    if response == 'y':
        # Tạo backup
        normalizer.create_backup()
        
        # Áp dụng thay đổi
        normalizer.apply_changes(dry_run=False)
        
        # In tóm tắt
        normalizer.print_summary()
        
        # Kiểm tra tính nhất quán
        normalizer.verify_consistency()
        
        print("\nHoàn thành chuẩn hóa tên file!")
    else:
        print("Hủy thực hiện.")

if __name__ == "__main__":
    main()