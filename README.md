# Hệ thống quản lý điểm ĐHNN

## Cấu trúc dự án

```
Diem_dhnn/
├── data_diem_dhnn/
│   ├── raw/                    # Dữ liệu gốc (.xls files)
│   └── processing/             # Dữ liệu đã xử lý
│       └── output_direct.xlsx  # File tổng hợp
├── direct_processor.py         # Xử lý dữ liệu từ .xls
├── app.py           # Ứng dụng Streamlit
└── file_normalizer.py         # Chuẩn hóa tên file
```

## Cách sử dụng

### 1. Xử lý dữ liệu
```bash
python direct_processor.py
```

### 2. Chạy ứng dụng
```bash
streamlit run app.py --server.port 8503
```

### 3. Truy cập
http://localhost:8503

## Tính năng

- 📊 Thống kê tổng quan
- 🔍 Tìm kiếm theo tên/mã SV  
- 📋 Lọc dữ liệu nâng cao
- 📤 Xuất CSV/JSON
