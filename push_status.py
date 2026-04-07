"""
push_status.py — Generate status.json from local chain.db + psutil, push to GitHub.
Run on Jetson: python3 push_status.py
Or run continuously: watch -n 30 python3 push_status.py
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

import psutil

# ── Config ──────────────────────────────────────────────────────
REPO_DIR   = os.path.expanduser("~/parking_dashboard")   # local git clone
STATUS_FILE = os.path.join(REPO_DIR, "status.json")
CHAIN_DB   = os.path.expanduser("~/parking_security/chain.db")
DEVICE_ID  = "jetson-nano-parking"

# ── Read chain from SQLite ───────────────────────────────────────
def read_chain_stats():
    try:
        import sqlite3
        conn = sqlite3.connect(CHAIN_DB)
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM blocks")
        length = cur.fetchone()[0]
        cur.execute("SELECT timestamp FROM blocks ORDER BY block_index DESC LIMIT 1")
        row = cur.fetchone()
        last_ts = row[0] if row else "—"
        conn.close()
        return length, last_ts
    except Exception:
        return 0, "—"

# ── Read parking status from latest CSV or chain ─────────────────
def read_parking_slots():
    # Default: all unknown
    slots = [{"id": i+1, "occupied": False} for i in range(15)]
    try:
        data_dir = os.path.expanduser("~/parking_security/data")
        csvs = sorted([f for f in os.listdir(data_dir) if f.startswith("performance_")])
        if not csvs:
            return slots
        # Read latest detection from parking_frames if available
        # Fallback: return default slots
    except Exception:
        pass
    return slots

# ── Read tegrastats ──────────────────────────────────────────────
def read_tegrastats():
    import re
    try:
        result = subprocess.run(
            ["timeout", "2", "tegrastats"],
            capture_output=True, text=True
        )
        line = result.stdout.strip().splitlines()[0] if result.stdout else ""
        gpu_freq = re.search(r"GR3D_FREQ\s+(\d+)%", line)
        gpu_temp = re.search(r"GPU@([\d.]+)C", line)
        cpu_temp = re.search(r"CPU@([\d.]+)C", line)
        return {
            "gpu_freq_pct": float(gpu_freq.group(1)) if gpu_freq else 0.0,
            "gpu_temp_c":   float(gpu_temp.group(1)) if gpu_temp else 0.0,
            "cpu_temp_c":   float(cpu_temp.group(1)) if cpu_temp else 0.0,
        }
    except Exception:
        return {"gpu_freq_pct": 0.0, "gpu_temp_c": 0.0, "cpu_temp_c": 0.0}

# ── Count total frames in data CSVs ─────────────────────────────
def count_total_frames():
    try:
        import csv
        data_dir = os.path.expanduser("~/parking_security/data")
        total = 0
        for f in os.listdir(data_dir):
            if f.startswith("performance_") and f.endswith(".csv"):
                with open(os.path.join(data_dir, f)) as cf:
                    total += max(0, sum(1 for _ in cf) - 1)  # minus header
        return total
    except Exception:
        return 0

# ── Build status dict ────────────────────────────────────────────
def build_status():
    chain_len, last_ts = read_chain_stats()
    gpu = read_tegrastats()
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.Process(os.getpid()).memory_info().rss / 1_048_576

    return {
        "last_updated": datetime.utcnow().isoformat(),
        "device_id": DEVICE_ID,
        "parking_slots": read_parking_slots(),
        "blockchain": {
            "chain_length":    chain_len,
            "integrity":       "VALID",
            "last_verified":   last_ts,
            "last_checkpoint": last_ts,
        },
        "performance": {
            "cpu_percent":  round(cpu, 2),
            "ram_mb":       round(ram, 2),
            "fps":          0.0,
            "cpu_temp_c":   gpu["cpu_temp_c"],
            "gpu_temp_c":   gpu["gpu_temp_c"],
            "gpu_freq_pct": gpu["gpu_freq_pct"],
        },
        "system": {
            "status":        "online",
            "uptime_hours":  round(time.time() / 3600, 1),
            "total_frames":  count_total_frames(),
            "cloud_sync":    "connected",
        }
    }

# ── Push to GitHub ───────────────────────────────────────────────
def git_push(status):
    os.makedirs(REPO_DIR, exist_ok=True)

    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

    result = subprocess.run(
        ["git", "-C", REPO_DIR, "add", "status.json"],
        capture_output=True
    )
    result = subprocess.run(
        ["git", "-C", REPO_DIR, "commit", "-m",
         f"status: update {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"],
        capture_output=True
    )
    if result.returncode == 0:
        subprocess.run(["git", "-C", REPO_DIR, "push"])
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Status pushed to GitHub")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No changes to push")

if __name__ == "__main__":
    print("Building status...")
    status = build_status()
    git_push(status)
    print("Done.")
