from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

DATA_DIR = Path("data")
CHUNK_ROWS = 250_000


def convert_all_parquet() -> None:
    parquet_files = sorted(DATA_DIR.glob("yellow_tripdata_*.parquet"))
    if not parquet_files:
        print("Không tìm thấy file yellow_tripdata_*.parquet trong thư mục data/")
        return

    for pq_path in parquet_files:
        csv_path = pq_path.with_suffix(".csv")
        pf = pq.ParquetFile(pq_path)
        total_rows = pf.metadata.num_rows

        # Ghi theo từng batch để không ngốn RAM khi xuất CSV lớn
        first_batch = True
        written = 0
        for batch in pf.iter_batches(batch_size=CHUNK_ROWS):
            df_chunk = batch.to_pandas()
            df_chunk.to_csv(
                csv_path,
                mode="w" if first_batch else "a",
                header=first_batch,
                index=False,
                encoding="utf-8",
            )
            first_batch = False
            written += len(df_chunk)

        print(f"[CSV] {csv_path.name}: {written:,} / {total_rows:,} rows")


if __name__ == "__main__":
    convert_all_parquet()