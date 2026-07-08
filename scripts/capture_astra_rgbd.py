from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "sessions"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock Astra RGB-D capture session.")
    parser.add_argument("--session_id", required=True)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    session_dir = DATA_DIR / args.session_id
    depth_dir = session_dir / "depth_frames"
    session_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)

    total_frames = args.duration * args.fps
    metadata = {
        "session_id": args.session_id,
        "device": "Orbbec Astra Pro S M",
        "mode": "mock_capture",
        "duration": args.duration,
        "fps": args.fps,
        "total_frames": total_frames,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "note": "Replace this script with OpenNI2 / Orbbec SDK RGB-D capture.",
    }
    (session_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    intrinsics = {"fx": 580.0, "fy": 580.0, "cx": 320.0, "cy": 240.0, "depth_scale": 0.001}
    (session_dir / "camera_intrinsics.json").write_text(json.dumps(intrinsics, ensure_ascii=False, indent=2), encoding="utf-8")

    with (session_dir / "timestamps.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_id", "time_sec", "rgb_file", "depth_file"])
        for frame_id in range(total_frames):
            writer.writerow([frame_id, round(frame_id / args.fps, 4), "rgb.mp4", f"depth_frames/depth_{frame_id:06d}.npy"])

    # Placeholder RGB/depth files for workflow visibility.
    (session_dir / "rgb.mp4").write_text("mock rgb video placeholder", encoding="utf-8")
    for frame_id in range(min(total_frames, 10)):
        (depth_dir / f"depth_{frame_id:06d}.npy").write_text("mock depth frame placeholder", encoding="utf-8")

    print(f"Mock RGB-D session created: {session_dir.relative_to(ROOT)}")
    print(f"Frames: {total_frames}")


if __name__ == "__main__":
    main()
