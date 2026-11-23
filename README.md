# Multi-Table Bulk Insert Benchmark (Python + SQLite)

So sánh hiệu năng 2 cách nạp **13,069,067 dòng** dữ liệu **NYC TLC Yellow Taxi (2024-01 → 2024-04)** vào database SQLite nhiều bảng (`zones`, `payments`, `trips`) bằng Python thuần.

> **Kết luận nhanh:** gom transaction theo chunk lớn kết hợp WAL nhanh hơn khoảng **1.4 lần** (giảm ~28.7% thời gian) so với commit từng batch nhỏ, mà dung lượng file DB không đổi.

## Hai phương pháp được so sánh

| | Cách 1: Batch nhỏ | Cách 2: Bulk chunk |
| :--- | :--- | :--- |
| Script | `src/insert_batch_small.py` | `src/insert_bulk_chunk.py` |
| Kích thước lô | 1,000 dòng | 50,000 dòng |
| Commit | Sau mỗi batch | Gom transaction theo file |
| Journal mode | Mặc định | `PRAGMA journal_mode = WAL` |
| Synchronous | Mặc định | `PRAGMA synchronous = NORMAL` |

## Kết quả

| Phương pháp | Tổng dòng | Thời gian | Tốc độ trung bình | File DB |
| :--- | :---: | :---: | :---: | :---: |
| Cách 1: Batch 1k | 13,069,067 | 253.68s | ~51,518 rows/s | 1,392.2 MB |
| Cách 2: Bulk 50k + WAL | 13,069,067 | 180.81s | ~72,281 rows/s | 1,392.2 MB |

**Vì sao Cách 2 nhanh hơn?**
- Ít lần `commit()` hơn nhiều (khoảng 13,000 lần ở Cách 1 so với vài lần ở Cách 2), nên giảm số lần ghi và `fsync` xuống đĩa.
- WAL ghi tuần tự vào file log thay vì ghi đè trực tiếp vào file DB.
- `synchronous = NORMAL` bỏ bớt các lần `fsync` không cần thiết khi nạp dữ liệu.

**Đánh đổi cần biết:** với WAL, `synchronous = NORMAL` vẫn không làm hỏng database khi mất điện đột ngột, nhưng có thể mất các transaction cuối chưa kịp checkpoint. Phù hợp với tác vụ nạp dữ liệu có thể chạy lại, không nên dùng cho dữ liệu giao dịch quan trọng.

Phân tích chi tiết ưu/nhược điểm và số liệu từng file: xem [REPORT.md](REPORT.md).

## Môi trường test

- CPU / RAM: `<điền>`
- Ổ đĩa: `<SSD / HDD / NVMe>`
- OS: `<điền>`
- Python: `<phiên bản>`, SQLite: `<phiên bản>`

> Kết quả phụ thuộc mạnh vào ổ đĩa và cấu hình máy, nên số liệu trên chỉ mang tính so sánh tương đối giữa 2 cách.

## Yêu cầu

- Python 3.x
- Thư viện: `<ví dụ: pandas, pyarrow>`

```bash
pip install <các thư viện cần thiết>
```

## Cấu trúc thư mục

```text
multi-table-bulk-insert/
├── data/                        # Chứa .parquet / .csv / taxi_zone_lookup.csv (đã .gitignore)
├── src/
│   ├── convert_parquet_to_csv.py
│   ├── insert_batch_small.py
│   └── insert_bulk_chunk.py
├── REPORT.md                    # Báo cáo đầy đủ: hướng dẫn, schema, kết quả benchmark
└── README.md
```

## Dữ liệu

- Nguồn: [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
  - `yellow_tripdata_2024-01` → `2024-04` (mỗi file khoảng 2.96M – 3.58M dòng, tổng hơn 13M dòng)
  - `taxi_zone_lookup.csv`
- Đặt tất cả file vào thư mục `data/`.
- (Tùy chọn) Bản lưu trữ trên Google Drive: `<dán link nếu có>`

## Hướng dẫn chạy nhanh

**1. Chuyển các file `.parquet` sang `.csv`:**

```bash
python src/convert_parquet_to_csv.py
```

**2. Chạy Cách 1 (Batch 1k, commit từng lô):**

```bash
python src/insert_batch_small.py
```

**3. Chạy Cách 2 (Bulk 50k + Transaction + WAL):**

```bash
python src/insert_bulk_chunk.py
```

> Nên xoá file `.db` cũ (hoặc dùng file DB riêng cho mỗi cách) trước khi chạy lại để kết quả so sánh công bằng.

## License

`<MIT / khác>`
