import time
from db_utils import insert_sqlite, tamper_row, recompute_hash_for_row

def run_experiment(blockchain, n=20, tamper_after=0):
    sqlite_times = []
    blockchain_times = []
    for i in range(n):
        step = f"Step {i+1}"
        t0 = time.time()
        rowid, ts, row_hash = insert_sqlite(step)
        t1 = time.time()
        sqlite_times.append(round(t1 - t0, 4))
        t2 = time.time()
        blockchain.add_block(row_hash)
        t3 = time.time()
        blockchain_times.append(round(t3 - t2, 4))
        time.sleep(0.01)
        if tamper_after and i+1 == tamper_after:
            tamper_row(1, "TAMPERED DATA")
    rows = get_all = None
    # compute integrity
    mismatches = 0
    for i in range(1, n+1):
        recomputed = recompute_hash_for_row(i)
        if recomputed is None:
            continue
        if blockchain.chain[i].data != recomputed:
            mismatches += 1
    integrity_percent = round(((n - mismatches) / n) * 100, 2) if n else 0
    avg_sql = round(sum(sqlite_times)/len(sqlite_times), 4) if sqlite_times else 0
    avg_bc = round(sum(blockchain_times)/len(blockchain_times), 4) if blockchain_times else 0
    return {"num_transactions": n, "avg_sqlite_time": avg_sql, "avg_blockchain_time": avg_bc, "integrity_percent": integrity_percent, "tampered": tamper_after}
