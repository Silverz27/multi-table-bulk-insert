# Multi-Table Bulk Insert Benchmark (Python)

So sánh 2 cách nạp thủ công **13,069,067 dòng** dữ liệu **NYC TLC Yellow Taxi (`2024-01` – `2024-04`)** vào database nhiều bảng (`zones`, `payments`, `trips`) bằng Python:
- **Cách 1 (`src/insert_batch_small.py`):** Batch nhỏ `1,000` dòng, `commit()` sau mỗi batch.
- **Cách 2 (`src/insert_bulk_chunk.py`):** Chunk lớn `50,000` dòng, gom transaction theo file kết hợp `PRAGMA journal_mode = WAL` và `PRAGMA synchronous = NORMAL`.

## Cấu trúc thư mục
```text
multi-table-bulk-insert/
├── data/                        # Thư mục chứa .parquet / .csv / taxi_zone_lookup.csv (bỏ qua qua .gitignore)
├── src/
│   ├── convert_parquet_to_csv.py
│   ├── insert_batch_small.py
│   └── insert_bulk_chunk.py
├── REPORT.md                    # Báo cáo đầy đủ hướng dẫn, schema và kết quả benchmark
└── README.md

## Dữ liệu
Nguồn: NYC TLC Trip Record Data (yellow_tripdata_2024-01 đến 2024-04, mỗi file ~2.96M–3.58M dòng; tổng > 13M dòng) + taxi_zone_lookup.csv.

(Tùy chọn) Bản lưu trữ dữ liệu trên Google Drive: <dán link Google Drive nếu có>.

## Hướng dẫn chạy nhanh
1. Chuyển các file yellow_tripdata_2024-*.parquet trong data/ sang .csv
python src/convert_parquet_to_csv.py

2. Chạy Cách 1 (Batch 1k, commit từng lô)
python src/insert_batch_small.py

3. Chạy Cách 2 (Bulk 50k + Transaction + WAL)
python src/insert_bulk_chunk.py

## Tóm tắt kết quả
Phương pháp,Tổng dòng,Thời gian,Tốc độ trung bình,File DB
| :--- | :---: | :---: |
Cách 1: Batch 1k,"13,069,067",253.68s,"~51,518 rows/s","1,392.2 MB"
Cách 2: Bulk 50k + WAL,"13,069,067",180.81s,"~72,284 rows/s","1,392.2 MB"

Xem phân tích chi tiết ưu/nhược điểm và bảng số liệu từng file tại REPORT.md.
