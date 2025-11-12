import sqlite3, hashlib, time, os
DB_PATH = os.path.join(os.path.dirname(__file__), 'production_log.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS production_log (id INTEGER PRIMARY KEY AUTOINCREMENT, step TEXT, timestamp REAL, row_hash TEXT)")
    conn.commit()
    conn.close()

def compute_hash(step, timestamp):
    return hashlib.sha256(f"{step}|{timestamp}".encode()).hexdigest()

def insert_sqlite(step):
    ts = time.time()
    row_hash = compute_hash(step, ts)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO production_log (step, timestamp, row_hash) VALUES (?, ?, ?)", (step, ts, row_hash))
    conn.commit()
    rowid = c.lastrowid
    conn.close()
    return rowid, ts, row_hash

def get_all_rows():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, step, timestamp, row_hash FROM production_log ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def tamper_row(rowid, new_step):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE production_log SET step = ? WHERE id = ?", (new_step, rowid))
    conn.commit()
    ok = c.rowcount > 0
    conn.close()
    return ok

def recompute_hash_for_row(rowid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT step, timestamp FROM production_log WHERE id = ?", (rowid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    step, ts = row
    return compute_hash(step, ts)
