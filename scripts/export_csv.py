from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "outputs" / "csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export final motion CSV.")
    parser.add_argument("--session_id", required=True)
    args = parser.parse_args()

    clean_path = CSV_DIR / f"{args.session_id}_clean_3d.csv"
    raw_path = CSV_DIR / f"{args.session_id}_raw_3d.csv"
    source = clean_path if clean_path.exists() else raw_path
    if not source.exists():
        raise FileNotFoundError("No raw or clean 3D CSV found. Run reconstruction first.")

    export_path = CSV_DIR / f"{args.session_id}_motion_export.csv"
    shutil.copyfile(source, export_path)
    print(f"CSV exported: {export_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
