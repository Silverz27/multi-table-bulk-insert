from __future__ import annotations

import csv
import sqlite3
import time
from pathlib import Path

DATA_DIR = Path("D:/multi-table-bulk-insert/data")
DB_PATH = Path("D:/multi-table-bulk-insert/benchmark/warehouse_bulk_chunk.db")
CHUNK_SIZE = 50_000


def _to_int(val: str | None, default: int) -> int:
    if val is None or val.strip() == "":
        return default
    try:
        return int(float(val))
    except ValueError:
        return default


def _to_float(val: str | None, default: float = 0.0) -> float:
    if val is None or val.strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default


def init_db_fast(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = -65536;
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS zones (
            location_id INTEGER PRIMARY KEY,
            borough TEXT,
            zone_name TEXT,
            service_zone TEXT
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_type INTEGER PRIMARY KEY,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trips (
            trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pickup_dt TEXT NOT NULL,
            dropoff_dt TEXT NOT NULL,
            pu_location_id INTEGER NOT NULL,
            do_location_id INTEGER NOT NULL,
            payment_type INTEGER NOT NULL,
            passenger_count REAL,
            trip_distance REAL,
            fare_amount REAL NOT NULL,
            total_amount REAL,
            source_file TEXT NOT NULL,
            FOREIGN KEY (pu_location_id) REFERENCES zones(location_id),
            FOREIGN KEY (do_location_id) REFERENCES zones(location_id),
            FOREIGN KEY (payment_type) REFERENCES payments(payment_type)
        );
    """)

    zones_map: dict[int, tuple[int, str, str, str]] = {
        264: (264, "Unknown", "N/A", "N/A"),
        265: (265, "Unknown", "Outside of NYC", "N/A"),
    }
    zone_csv = DATA_DIR / "taxi_zone_lookup.csv"
    if zone_csv.exists():
        with zone_csv.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                lid = _to_int(r.get("LocationID"), -1)
                if lid >= 0:
                    zones_map[lid] = (
                        lid,
                        r.get("Borough", ""),
                        r.get("Zone", ""),
                        r.get("service_zone", ""),
                    )

    conn.executemany(
        "INSERT OR IGNORE INTO zones (location_id, borough, zone_name, service_zone) VALUES (?, ?, ?, ?)",
        list(zones_map.values()),
    )

    payments_seed = [
        (0, "Flex Fare trip"),
        (1, "Credit card"),
        (2, "Cash"),
        (3, "No charge"),
        (4, "Dispute"),
        (5, "Unknown"),
        (6, "Voided trip"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO payments (payment_type, description) VALUES (?, ?)",
        payments_seed,
    )
    conn.commit()


def insert_file_large_chunk(conn: sqlite3.Connection, csv_path: Path) -> int:
    sql = """
        INSERT INTO trips (
            pickup_dt, dropoff_dt, pu_location_id, do_location_id,
            payment_type, passenger_count, trip_distance,
            fare_amount, total_amount, source_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    chunk = []
    inserted = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        conn.execute("BEGIN TRANSACTION;")
        try:
            for row in reader:
                pu_id = _to_int(row.get("PULocationID"), 264)
                do_id = _to_int(row.get("DOLocationID"), 264)
                pay_type = _to_int(row.get("payment_type"), 5)
                if pay_type not in range(0, 7):
                    pay_type = 5

                chunk.append((
                    row.get("tpep_pickup_datetime", ""),
                    row.get("tpep_dropoff_datetime", ""),
                    pu_id,
                    do_id,
                    pay_type,
                    _to_float(row.get("passenger_count"), 0.0),
                    _to_float(row.get("trip_distance"), 0.0),
                    _to_float(row.get("fare_amount"), 0.0),
                    _to_float(row.get("total_amount"), 0.0),
                    csv_path.name,
                ))

                if len(chunk) >= CHUNK_SIZE:
                    conn.executemany(sql, chunk)
                    inserted += len(chunk)
                    chunk.clear()

            if chunk:
                conn.executemany(sql, chunk)
                inserted += len(chunk)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return inserted


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    csv_files = sorted(DATA_DIR.glob("yellow_tripdata_*.csv"))
    conn = sqlite3.connect(DB_PATH)
    init_db_fast(conn)

    t_start = time.perf_counter()
    total_rows = 0

    for fp in csv_files:
        t0 = time.perf_counter()
        n = insert_file_large_chunk(conn, fp)
        dt = time.perf_counter() - t0
        total_rows += n
        print(f"[Bulk 50k] {fp.name}: {n:,} rows | {dt:.2f}s ({n / max(dt, 1e-6):,.0f} rows/s)")

    total_time = time.perf_counter() - t_start
    db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\n[SUMMARY - Cách 2] Tổng: {total_rows:,} rows | Thời gian: {total_time:.2f}s | DB: {db_size_mb:.1f} MB")
    conn.close()


if __name__ == "__main__":
    main()