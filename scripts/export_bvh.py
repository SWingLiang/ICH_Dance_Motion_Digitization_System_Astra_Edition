from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "outputs" / "csv"
BVH_DIR = ROOT / "outputs" / "bvh"

HIERARCHY = """HIERARCHY
ROOT Hips
{
  OFFSET 0.000000 0.000000 0.000000
  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
  JOINT Spine
  {
    OFFSET 0.000000 0.200000 0.000000
    CHANNELS 3 Zrotation Xrotation Yrotation
    JOINT Neck
    {
      OFFSET 0.000000 0.250000 0.000000
      CHANNELS 3 Zrotation Xrotation Yrotation
      JOINT Head
      {
        OFFSET 0.000000 0.150000 0.000000
        CHANNELS 3 Zrotation Xrotation Yrotation
        End Site
        {
          OFFSET 0.000000 0.100000 0.000000
        }
      }
    }
  }
  JOINT LeftUpLeg
  {
    OFFSET -0.100000 -0.100000 0.000000
    CHANNELS 3 Zrotation Xrotation Yrotation
    JOINT LeftLeg
    {
      OFFSET 0.000000 -0.350000 0.000000
      CHANNELS 3 Zrotation Xrotation Yrotation
      JOINT LeftFoot
      {
        OFFSET 0.000000 -0.350000 0.080000
        CHANNELS 3 Zrotation Xrotation Yrotation
        End Site
        {
          OFFSET 0.000000 -0.050000 0.120000
        }
      }
    }
  }
  JOINT RightUpLeg
  {
    OFFSET 0.100000 -0.100000 0.000000
    CHANNELS 3 Zrotation Xrotation Yrotation
    JOINT RightLeg
    {
      OFFSET 0.000000 -0.350000 0.000000
      CHANNELS 3 Zrotation Xrotation Yrotation
      JOINT RightFoot
      {
        OFFSET 0.000000 -0.350000 0.080000
        CHANNELS 3 Zrotation Xrotation Yrotation
        End Site
        {
          OFFSET 0.000000 -0.050000 0.120000
        }
      }
    }
  }
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Export simplified BVH from clean 3D motion CSV.")
    parser.add_argument("--session_id", required=True)
    args = parser.parse_args()

    BVH_DIR.mkdir(parents=True, exist_ok=True)
    clean_path = CSV_DIR / f"{args.session_id}_clean_3d.csv"
    raw_path = CSV_DIR / f"{args.session_id}_raw_3d.csv"
    source = clean_path if clean_path.exists() else raw_path
    if not source.exists():
        raise FileNotFoundError("No motion CSV found. Run reconstruction first.")

    df = pd.read_csv(source)
    hip = df[df["joint_name"] == "MidHip"].sort_values("frame_id")
    if hip.empty:
        raise ValueError("MidHip joint not found in CSV.")

    frames = []
    for _, row in hip.iterrows():
        # Root translation uses MidHip position; all rotations are zero in this V0.1 simplified export.
        root = [float(row["x"]), float(row["y"]), float(row["z"]), 0.0, 0.0, 0.0]
        rotations = [0.0, 0.0, 0.0] * 9
        frames.append(root + rotations)

    out_path = BVH_DIR / f"{args.session_id}.bvh"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(HIERARCHY)
        f.write("MOTION\n")
        f.write(f"Frames: {len(frames)}\n")
        f.write("Frame Time: 0.0333333\n")
        for frame in frames:
            f.write(" ".join(f"{value:.6f}" for value in frame) + "\n")

    print(f"Simplified BVH exported: {out_path.relative_to(ROOT)}")
    print("Note: V0.1 BVH uses root translation and zero rotations. Future versions should solve joint rotations with IK.")


if __name__ == "__main__":
    main()
