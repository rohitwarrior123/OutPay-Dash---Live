"""
update_data.py
---------------
Reads the master Excel file described in bot_config.json, converts the
relevant columns into JSON, writes it into the repo's /data folder, then
commits + pushes so Render picks up the refreshed data on redeploy.

Run once manually to test:
    python update_data.py --once

Run continuously (used by run_bot.bat):
    python update_data.py
"""
import json
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "bot_config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def read_excel(cfg):
    excel_path = cfg["excel_path"]
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found at: {excel_path}")

    df = pd.read_excel(
        excel_path,
        sheet_name=cfg.get("sheet_name", 0),
        header=cfg.get("header_row", 0),
        engine="openpyxl",
    )
    df.columns = [str(c).strip() for c in df.columns]
    return df


def map_columns(df, column_map):
    """Rename Excel headers -> dashboard field names, keeping only mapped columns
    that actually exist in the sheet (missing ones are skipped with a warning)."""
    rename = {}
    for field, excel_header in column_map.items():
        if excel_header in df.columns:
            rename[excel_header] = field
        else:
            print(f"[warn] column '{excel_header}' (-> {field}) not found in sheet; skipping")
    mapped = df[list(rename.keys())].rename(columns=rename)
    return mapped


def dataframe_to_json_records(df):
    # Make everything JSON-safe (dates, NaN, numpy types)
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d")
    out = out.where(pd.notnull(out), None)
    return json.loads(out.to_json(orient="records"))


def build_payload(records):
    return {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "row_count": len(records),
        "rows": records,
    }


def write_json(cfg, payload):
    out_path = os.path.normpath(os.path.join(SCRIPT_DIR, cfg["output_path"]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_path


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[git] command failed: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result.returncode == 0


def git_commit_and_push(cfg):
    git_cfg = cfg["git"]
    repo_dir = os.path.normpath(os.path.join(SCRIPT_DIR, git_cfg["repo_dir"]))
    run(["git", "add", "data/dashboard_data.json"], cwd=repo_dir)
    committed = run(["git", "commit", "-m", git_cfg["commit_message"]], cwd=repo_dir)
    if not committed:
        print("[git] nothing new to commit")
        return
    run(["git", "push", git_cfg["remote"], git_cfg["branch"]], cwd=repo_dir)


def do_one_cycle(cfg):
    try:
        df = read_excel(cfg)
        mapped = map_columns(df, cfg["column_map"])
        records = dataframe_to_json_records(mapped)
        payload = build_payload(records)
        out_path = write_json(cfg, payload)
        print(f"[ok] wrote {len(records)} rows -> {out_path}")
        git_commit_and_push(cfg)
    except Exception as e:
        print(f"[error] {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="run a single cycle and exit")
    args = parser.parse_args()

    cfg = load_config()
    interval_sec = int(cfg.get("poll_interval_minutes", 5)) * 60

    if args.once:
        do_one_cycle(cfg)
        return

    while True:
        do_one_cycle(cfg)
        print(f"[wait] sleeping {interval_sec}s ...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()
