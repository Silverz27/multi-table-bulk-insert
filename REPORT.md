# Báo cáo: Nạp dữ liệu quy mô lớn vào Database nhiều bảng bằng Python

## 1. Dữ liệu sử dụng
- Bộ dữ liệu: NYC TLC Yellow Taxi (2024-01 đến 2024-04 + 	axi_zone_lookup.csv).
- Số dòng từng file (> 1 triệu dòng/file):
  - yellow_tripdata_2024-01.csv: **2,964,624** dòng
  - yellow_tripdata_2024-02.csv: **3,007,526** dòng
  - yellow_tripdata_2024-03.csv: **3,582,628** dòng
  - yellow_tripdata_2024-04.csv: **3,514,289** dòng
- Tổng quy mô (> 10 triệu dòng): **13,069,067** dòng.

## 2. Database nhiều bảng
- zones: danh mục khu vực (location_id PK).
- payments: danh mục thanh toán (payment_type PK).
- 	rips: bảng chuyến đi (	rip_id PK, pu_location_id FK, do_location_id FK, payment_type FK, source_file).

## 3. Hướng dẫn chạy
1. Đặt các file .parquet và 	axi_zone_lookup.csv vào thư mục data/.
2. Chuyển sang CSV: python src/convert_parquet_to_csv.py
3. Chạy Cách 1 (batch nhỏ 1,000 dòng, commit từng lô): python src/insert_batch_small.py
4. Chạy Cách 2 (chunk lớn 50,000 dòng, Transaction + WAL): python src/insert_bulk_chunk.py

## 4. Kết quả so sánh
| Chỉ tiêu | Cách 1 (Batch 1k, commit từng lô) | Cách 2 (Bulk 50k + Transaction/WAL) |
| :--- | :---: | :---: |
| Tổng số dòng | 13,069,067 | 13,069,067 |
| Tổng thời gian | **253.68s** (~51,518 rows/s) | **180.81s** (~72,284 rows/s) |
| Dung lượng DB | 1,392.2 MB | 1,392.2 MB |

- **Cách 1:** Ưu điểm là commit nhỏ thường xuyên, dễ theo dõi tiến độ; nhược điểm là commit nhiều lần (~13k lần) nên chậm hơn.
- **Cách 2:** Ưu điểm là giảm số lần commit và bật WAL nên nhanh hơn **72.87s** (~28.7%); nhược điểm là giữ transaction dài hơn theo từng file.
