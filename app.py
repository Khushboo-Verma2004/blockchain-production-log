import os, time
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from db_utils import init_db, insert_sqlite, get_all_rows, recompute_hash_for_row, tamper_row
from blockchain import Blockchain
from experiment import run_experiment

load_dotenv()
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "devsecret")

init_db()
sim_chain = Blockchain()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/add_step", methods=["POST"])
def api_add_step():
    data = request.get_json() or {}
    step = data.get("step", "").strip()
    if not step:
        return jsonify({"error": "step required"}), 400
    t0 = time.time()
    rowid, ts, row_hash = insert_sqlite(step)
    t1 = time.time()
    sqlite_time = round(t1 - t0, 4)
    t2 = time.time()
    blk = sim_chain.add_block(row_hash)
    t3 = time.time()
    blockchain_time = round(t3 - t2, 4)
    return jsonify({
        "rowid": rowid,
        "step": step,
        "timestamp": ts,
        "row_hash": row_hash,
        "sqlite_time": sqlite_time,
        "blockchain_time": blockchain_time,
        "block_index": blk.index,
        "block_hash": blk.hash
    })

@app.route("/api/data", methods=["GET"])
def api_data():
    rows = get_all_rows()
    formatted_rows = [{"id": r[0], "step": r[1], "timestamp": r[2], "row_hash": r[3]} for r in rows]
    bc_list = [{"index": b.index, "timestamp": b.timestamp, "data": b.data, "hash": b.hash} for b in sim_chain.chain]
    return jsonify({"sqlite": formatted_rows, "blockchain": bc_list})

@app.route("/api/tamper", methods=["POST"])
def api_tamper():
    data = request.get_json() or {}
    rowid = int(data.get("id", 0))
    new_step = data.get("new_step", f"TAMPERED at {time.time()}")
    ok = tamper_row(rowid, new_step)
    return jsonify({"tampered": ok, "id": rowid, "new_step": new_step})

@app.route("/api/check_integrity", methods=["GET"])
def api_check_integrity():
    rows = get_all_rows()
    total = len(rows)
    recomputed_matches = 0
    mismatches = []
    for r in rows:
        rowid, step, ts, stored_hash = r
        recomputed = recompute_hash_for_row(rowid)
        if stored_hash == recomputed:
            recomputed_matches += 1
        else:
            mismatches.append({"id": rowid, "stored_hash": stored_hash, "recomputed": recomputed, "step": step})
    integrity_percent = round((recomputed_matches / total) * 100, 2) if total else 0
    matched = 0
    for r in rows:
        idx = r[0]
        stored_hash = r[3]
        if idx < len(sim_chain.chain):
            if sim_chain.chain[idx].data == stored_hash:
                matched += 1
    transparency = round((matched / total) * 100, 2) if total else 0
    return jsonify({"total_rows": total, "integrity_percent": integrity_percent, "transparency_index_percent": transparency, "mismatches": mismatches})

@app.route("/api/experiment", methods=["POST"])
def api_experiment():
    data = request.get_json() or {}
    n = int(data.get("num_transactions", 20))
    tamper_after = int(data.get("tamper_after", 0))
    results = run_experiment(sim_chain, n, tamper_after)
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
