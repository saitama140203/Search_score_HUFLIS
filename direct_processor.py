#!/usr/bin/env python3
"""
Xử lý trực tiếp file Excel ĐHNN mà không qua DataFrame trung gian.
"""
import xlrd
from openpyxl import Workbook
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def process_dhnn_file(file_path):
    """Đọc và xử lý một file Excel ĐHNN theo cấu trúc thực tế."""
    try:
        wb = xlrd.open_workbook(str(file_path), on_demand=True, formatting_info=False)
        sh = wb.sheet_by_index(0)
        
        if sh.nrows < 10:
            wb.release_resources()
            return None
        
        header_row = None
        for r in range(min(15, sh.nrows)):
            row_text = ' '.join([str(sh.cell_value(r, c)) for c in range(min(5, sh.ncols))])
            if 'STT' in row_text and 'Mã SV' in row_text:
                header_row = r
                break
        
        if header_row is None:
            wb.release_resources()
            return None
        
        headers = []
        for c in range(sh.ncols):
            val = sh.cell_value(header_row, c)
            if val is None or str(val).strip() == '':
                headers.append('nan')
            else:
                header_str = str(val).replace('\n', ' ').strip()
                headers.append(header_str)
        
        data_rows = []
        for r in range(header_row + 1, sh.nrows - 2):
            row_data = []
            for c in range(sh.ncols):
                try:
                    val = sh.cell_value(r, c)
                    if isinstance(val, float):
                        if val == int(val):
                            val = int(val)
                    row_data.append(val if val is not None else '')
                except:
                    row_data.append('')
            
            if any(str(v).strip() for v in row_data if v != ''):
                data_rows.append(row_data)
        
        wb.release_resources()
        
        name_col_idx = None
        potential_name_cols = []
        
        for i, header in enumerate(headers):
            if 'Họ và tên' in header or 'Họ tên' in header:
                name_col_idx = i
            elif header == 'nan' or header == '':
                potential_name_cols.append(i)
        
        if name_col_idx is not None:
            for row in data_rows:
                name_parts = [str(row[name_col_idx]) if row[name_col_idx] else ""]
                
                for col_idx in potential_name_cols:
                    if abs(col_idx - name_col_idx) <= 5:
                        if row[col_idx] and str(row[col_idx]).strip():
                            val = str(row[col_idx]).strip()
                            if not val.replace('.', '').isdigit():
                                name_parts.append(val)
                
                combined_name = ' '.join(name_parts).strip()
                row[name_col_idx] = combined_name
            
            new_headers = []
            keep_cols = []
            for i, header in enumerate(headers):
                if header != 'nan' and header != '':
                    new_headers.append(header)
                    keep_cols.append(i)
                elif i == name_col_idx:
                    new_headers.append('Họ và tên')
                    keep_cols.append(i)
            
            new_data_rows = []
            for row in data_rows:
                new_row = [row[i] for i in keep_cols]
                new_data_rows.append(new_row)
            
            headers = new_headers
            data_rows = new_data_rows
        
        return headers, data_rows
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def main():
    """Xử lý tất cả file và ghi ra Excel."""
    base_path = Path('data_diem_dhnn')
    raw_path = base_path / 'raw'
    output_path = base_path / 'processing' / 'output_direct.xlsx'
    output_path.parent.mkdir(exist_ok=True)
    
    wb_out = Workbook()
    ws_all = wb_out.active
    ws_all.title = 'All Data'
    
    main_headers = ['STT', 'Mã SV', 'Họ và tên', 'Tổng số tín chỉ', 'Tổng số TCTL', 
                    'Điểm TBTL', 'Số TC học/thi lại', 'Học kỳ', 'Khóa', 'Môn học']
    ws_all.append(main_headers)
    
    row_count = 0
    success_count = 0
    fail_count = 0
    for file_path in raw_path.rglob('*.xls'):
        rel_path = file_path.relative_to(raw_path)
        parts = rel_path.parts
        
        if len(parts) != 3:
            continue
            
        semester = parts[0]
        khoa = parts[1]
        subject = file_path.stem
        
        print(f'Processing: {semester}/{khoa}/{subject}...', end=' ')
        
        result = process_dhnn_file(file_path)
        
        if result:
            headers, data_rows = result
            
            col_mapping = {}
            for i, h in enumerate(headers):
                h_clean = h.strip()
                if 'STT' in h_clean:
                    col_mapping[0] = i
                elif 'Mã SV' in h_clean or 'MSSV' in h_clean:
                    col_mapping[1] = i
                elif 'Họ và tên' in h_clean or 'Họ tên' in h_clean:
                    col_mapping[2] = i
                elif 'Tổng số tín chỉ' in h_clean or 'Tổng số\ntín chỉ' in h_clean:
                    col_mapping[3] = i
                elif 'TCTL' in h_clean:
                    col_mapping[4] = i
                elif 'Điểm TBTL' in h_clean or 'Điểm\nTBTL' in h_clean:
                    col_mapping[5] = i
                elif 'TC học/thi lại' in h_clean or 'học/thi lại' in h_clean:
                    col_mapping[6] = i
            
            for row_data in data_rows:
                out_row = [''] * len(main_headers)
                
                for out_idx, in_idx in col_mapping.items():
                    if in_idx < len(row_data):
                        out_row[out_idx] = row_data[in_idx]
                
                out_row[7] = semester.upper()
                out_row[8] = khoa.upper()
                out_row[9] = subject
                
                ws_all.append(out_row)
                row_count += 1
            
            success_count += 1
            print(f'✓ OK ({len(data_rows)} rows)')
        else:
            fail_count += 1
            print('✗ Failed')
    
    wb_out.save(output_path)
    
    print(f'\n{"="*60}')
    print('SUMMARY')
    print(f'{"="*60}')
    print(f'Files processed: {success_count + fail_count}')
    print(f'Success: {success_count}')
    print(f'Failed: {fail_count}')
    print(f'Total rows: {row_count}')
    print(f'Output: {output_path}')


if __name__ == '__main__':
    main()
