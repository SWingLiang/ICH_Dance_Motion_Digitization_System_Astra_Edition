from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "sessions"

BODY25_BASE = [
    (320, 120), (320, 170), (270, 175), (245, 235), (230, 295),
    (370, 175), (395, 235), (410, 295), (320, 300), (285, 305),
    (275, 390), (270, 470), (355, 305), (365, 390), (370, 470),
    (305, 110), (335, 110), (290, 120), (350, 120), (385, 500),
    (405, 500), (370, 492), (255, 500), (235, 500), (270, 492),
]


def make_frame_keypoints(frame_id: int):
    keypoints = []
    sway = math.sin(frame_id / 5.0) * 8
    lift = math.sin(frame_id / 8.0) * 5
    for joint_id, (u, v) in enumerate(BODY25_BASE):
        confidence = 0.92
        uu = u + sway * (1 if joint_id % 2 == 0 else -0.6)
        vv = v + lift
        keypoints.extend([round(uu, 3), round(vv, 3), confidence])
    return keypoints


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock OpenPose BODY_25 JSON generator.")
    parser.add_argument("--session_id", required=True)
    parser.add_argument("--openpose_path", default=None)
    parser.add_argument("--model", default="BODY_25")
    parser.add_argument("--use_gpu", action="store_true")
    args = parser.parse_args()

    session_dir = DATA_DIR / args.session_id
    json_dir = session_dir / "openpose_json"
    json_dir.mkdir(parents=True, exist_ok=True)

    frame_count = 60
    metadata_path = session_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        frame_count = min(int(metadata.get("total_frames", 60)), 120)

    for frame_id in range(frame_count):
        data = {
            "version": 1.3,
            "people": [
                {
                    "person_id": [-1],
                    "pose_keypoints_2d": make_frame_keypoints(frame_id),
                    "face_keypoints_2d": [],
                    "hand_left_keypoints_2d": [],
                    "hand_right_keypoints_2d": [],
                }
            ],
        }
        out_path = json_dir / f"frame_{frame_id:06d}_keypoints.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    print(f"Mock OpenPose {args.model} JSON written: {json_dir.relative_to(ROOT)}")
    print(f"GPU requested: {args.use_gpu}")
    print("Replace this script with OpenPoseDemo.exe subprocess call for real analysis.")


if __name__ == "__main__":
    main()
