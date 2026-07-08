from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "sessions"
OUTPUT_CSV_DIR = ROOT / "outputs" / "csv"

BODY25_NAMES = [
    "Nose", "Neck", "RShoulder", "RElbow", "RWrist", "LShoulder", "LElbow", "LWrist",
    "MidHip", "RHip", "RKnee", "RAnkle", "LHip", "LKnee", "LAnkle", "REye", "LEye",
    "REar", "LEar", "LBigToe", "LSmallToe", "LHeel", "RBigToe", "RSmallToe", "RHeel",
]


def load_keypoints(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    people = data.get("people", [])
    if not people:
        return []
    flat = people[0].get("pose_keypoints_2d", [])
    keypoints = []
    for joint_id in range(0, min(len(flat) // 3, len(BODY25_NAMES))):
        u, v, confidence = flat[joint_id * 3: joint_id * 3 + 3]
        keypoints.append((joint_id, BODY25_NAMES[joint_id], float(u), float(v), float(confidence)))
    return keypoints


def sample_mock_depth(u: float, v: float, frame_id: int) -> float:
    # Mock depth in millimeters. Later replace with aligned Astra depth image sampling.
    neighborhood = [1800 + (u % 40) * 2 + (v % 30) + frame_id * 3 + offset for offset in [-8, -3, 0, 5, 9]]
    return float(median(neighborhood))


def back_project(u: float, v: float, depth_mm: float, fx: float, fy: float, cx: float, cy: float):
    z = depth_mm / 1000.0
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    return x, y, z


def main() -> None:
    parser = argparse.ArgumentParser(description="Lift OpenPose 2D keypoints to mock 3D coordinates with depth.")
    parser.add_argument("--session_id", required=True)
    args = parser.parse_args()

    session_dir = DATA_DIR / args.session_id
    json_dir = session_dir / "openpose_json"
    intrinsics_path = session_dir / "camera_intrinsics.json"
    OUTPUT_CSV_DIR.mkdir(parents=True, exist_ok=True)

    if not json_dir.exists():
        raise FileNotFoundError(f"OpenPose JSON directory not found: {json_dir}")

    if intrinsics_path.exists():
        intrinsics = json.loads(intrinsics_path.read_text(encoding="utf-8"))
    else:
        intrinsics = {"fx": 580.0, "fy": 580.0, "cx": 320.0, "cy": 240.0}

    out_path = OUTPUT_CSV_DIR / f"{args.session_id}_raw_3d.csv"
    fieldnames = [
        "frame_id", "time_sec", "person_id", "joint_id", "joint_name", "u", "v", "confidence",
        "depth_mm", "x", "y", "z", "valid"
    ]

    json_files = sorted(json_dir.glob("*_keypoints.json"))
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for frame_id, json_file in enumerate(json_files):
            for joint_id, name, u, v, conf in load_keypoints(json_file):
                depth_mm = sample_mock_depth(u, v, frame_id)
                x, y, z = back_project(u, v, depth_mm, intrinsics["fx"], intrinsics["fy"], intrinsics["cx"], intrinsics["cy"])
                writer.writerow({
                    "frame_id": frame_id,
                    "time_sec": round(frame_id / 30.0, 4),
                    "person_id": 0,
                    "joint_id": joint_id,
                    "joint_name": name,
                    "u": round(u, 3),
                    "v": round(v, 3),
                    "confidence": round(conf, 4),
                    "depth_mm": round(depth_mm, 3),
                    "x": round(x, 6),
                    "y": round(y, 6),
                    "z": round(z, 6),
                    "valid": int(conf > 0.05 and depth_mm > 0),
                })

    print(f"3D reconstruction CSV written: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
