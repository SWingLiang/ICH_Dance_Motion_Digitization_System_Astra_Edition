from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "outputs" / "csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Smooth raw 3D motion CSV.")
    parser.add_argument("--session_id", required=True)
    parser.add_argument("--method", default="moving_average")
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()

    raw_path = CSV_DIR / f"{args.session_id}_raw_3d.csv"
    clean_path = CSV_DIR / f"{args.session_id}_clean_3d.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw 3D CSV not found: {raw_path}")

    df = pd.read_csv(raw_path)
    if args.method == "moving_average":
        window = max(1, args.window)
        for axis in ["x", "y", "z"]:
            df[axis] = df.groupby("joint_id")[axis].transform(
                lambda s: s.rolling(window=window, min_periods=1, center=True).mean()
            )
        df["optimization_method"] = f"moving_average_{window}"
    else:
        df["optimization_method"] = "none"

    df.to_csv(clean_path, index=False)
    print(f"Clean 3D CSV written: {clean_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
